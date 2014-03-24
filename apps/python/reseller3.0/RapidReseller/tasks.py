#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.
""" Response handlers for offline task queues.

    TaskCleanUp: Purge a given Google Apps customer instance.
"""

__author__ = 'richieforeman@google.com (Richie Foreman)'

import httplib2
import time

import logging
from app import BaseHandler
from app import WSGIApplication

from constants import ResellerPlanName
from constants import ResellerSKU
from constants import ResellerRenewalType
from constants import ResellerProduct
from constants import ResellerDeletionType

from google.appengine.api import memcache

import settings

from apiclient.discovery import build
from apiclient.http import BatchHttpRequest

from oauth2client.client import SignedJwtAssertionCredentials

from utils import get_credentials

import webapp2


class TaskCleanup(BaseHandler):

    def post(self):
        domain = self.request.get("domain")
        logging.info("Execing cleanup task for domain (%s)" % domain)

        http = httplib2.Http()
        credentials = get_credentials(settings.RESELLER_ADMIN)
        credentials.authorize(http)

        service = build("reseller", settings.RESELLER_API_VERSION, http=http)

        response = service.customers().get(
            customerId=domain).execute(num_retries=5)

        def delete_sub_callback(request_id, response, exception):
            # just log the exception.
            logging.exception(exception)
            pass

        if not response.get("alternateEmail"):
            logging.info("Skipping cleanup, customer not resold..")
            exit()

        response = service.subscriptions().list(
            customerId=domain,
            maxResults=100).execute(num_retries=5)

        # resort the subscriptions and bump GAFB subs to the bottom
        all_subscriptions = response['subscriptions']

        batch = BatchHttpRequest(callback=delete_sub_callback)

        logging.info("Purging %d subs" % len(all_subscriptions))

        apps_subscription = None

        for subscription in all_subscriptions:
            if subscription['status'] in [ResellerDeletionType.Cancel,
                                          ResellerDeletionType.Suspend,
                                          ResellerDeletionType.Downgrade]:
                logging.info("Skipping subscription, in deleted state")
                continue

            # GAfB cannot be deleted in the batch request with the others.
            if subscription['skuId'] == ResellerSKU.GoogleApps:
                apps_subscription = subscription
                continue

            # Google-Drive-storage / Google-Vault must be cancelled.
            request = service.subscriptions().delete(
                customerId=domain,
                subscriptionId=subscription['subscriptionId'],
                deletionType=ResellerDeletionType.Cancel)

            batch.add(request)

        batch.execute(http=http)

        # Delete
        if apps_subscription:
            service.subscriptions().delete(
                customerId=domain,
                subscriptionId=apps_subscription['subscriptionId'],
                deletionType=ResellerDeletionType.Suspend
            ).execute(num_retries=5)

app = WSGIApplication(routes=[
    (r'/tasks/cleanup', TaskCleanup),
], config=settings.WEBAPP2_CONFIG)