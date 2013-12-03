#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.

"""
      DISCLAIMER:

   (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
   WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
   WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
   PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND

   (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
   OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
   DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
   GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
   THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR
   ITS DERIVATIVES.
   """

__author__ = 'richieforeman@google.com (Richie Foreman)'

import httplib2
import time

import logging
from app import wsgi
from app import BaseHandler

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


@wsgi.route("/tasks/cleanup")
class TaskCleanup(BaseHandler):
    def get(self):
        self.post()
    def post(self):
        domain = self.request.get("domain")
        logging.info("Execing cleanup task for domain (%s)" % domain)

        http = httplib2.Http()
        httplib2.debuglevel = 4
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
        subs = sorted(
            response['subscriptions'],
            cmp=lambda a, b: int(a['skuId'] == ResellerSKU.GoogleApps) - 1)

        batch = BatchHttpRequest(callback=delete_sub_callback)

        logging.info("Purging %d subs" % len(subs))

        for s in subs:
            if s['status'] in [ResellerDeletionType.Cancel,
                               ResellerDeletionType.Suspend,
                               ResellerDeletionType.Downgrade]:
                logging.info("Skipping subscription, in deleted state")
                continue

            # Google-Drive-storage / Google-Vault must be cancelled.
            deletionType = ResellerDeletionType.Cancel

            # GAfB cannot be 'cancelled', and must be 'suspended'
            if s['skuId'] == ResellerSKU.GoogleApps:
                deletionType = ResellerDeletionType.Suspend

            request = service.subscriptions().delete(
                customerId=domain,
                subscriptionId=s['subscriptionId'],
                deletionType=deletionType)

            batch.add(request)

        batch.execute(http=http)




