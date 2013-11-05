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
"""
    Provides the ability to transfer resold Google Apps customers
    in bulk via the Reseller API

    Setup:
        - Create an OAuth2 Project and enable the Reseller API
        - Create a client id for "installed applications"
        - Download the client_secrets.json file and place it in the same dir.
        - Run the script to authorize the script.
        - The script will need to be authorized as a Domain Administrator
        - Credentials are stored permanently in an 'auth.dat' file.

    Usage:
        - Copy these Google Spreadsheet from here:
          https://docs.google.com/a/google.com/spreadsheet/ccc
          ?key=0ApbFnEPbWYupdFZZNjZQdEF0TnROcU1CUnRNNTQyeXc&usp=drive_web#gid=0
        - Complete the spreadsheet
        - Run the script "python import.py --in_file <csvfile.csv>

"""
from argparse import ArgumentParser

from apiclient.discovery import build

import csv

import logging
import httplib2
import time

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
try:
    from oauth2client.tools import run_parser
except ImportError:
    # hmm, seems like a bug in oauth2client to me.
    from oauth2client.tools import argparser as run_parser

CLIENT_SECRETS = 'client_secrets.json'
SCOPES = [
    'https://www.googleapis.com/auth/apps.order'
]
RESELLER_API_VERSION = "v1"
NUM_RETRIES = 5
CLIENT_SECRETS = 'client_secrets.json'
THROTTLE_SLEEP = 1
REQUIRED_FIELDS = [
    'customerAuthToken',
    'subscriptionId',
    'skuId',
    'plan.planName',
    'plan.isCommitmentPlan',
    'renewalSettings.renewalType',
    'seats.numberOfSeats',
    'seats.maximumNumberOfSeats'
]
VALID_SKUS = [
    "Google-Apps-For-Business",
    "Google-Drive-storage-20GB",
    "Google-Drive-storage-50GB",
    "Google-Drive-storage-200GB",
    "Google-Drive-storage-400GB",
    "Google-Drive-storage-1TB",
    "Google-Drive-storage-2TB",
    "Google-Drive-storage-4TB",
    "Google-Drive-storage-8TB",
    "Google-Drive-storage-16TB",
    "Google-Vault",
]
VALID_PLANNAMES = [
    'ANNUAL',
    'FLEXIBLE',
    'TRIAL'
]
VALID_RENEWAL_TYPES = [
    'AUTO_RENEW',
    'RENEW_CURRENT_USERS',
    'SWITCH_TO_PAY_AS_YOU_GO',
    'CANCEL'
]

http = httplib2.Http()


def get_credentials(args):
    storage = Storage("auth.dat")
    credentials = storage.get()

    if not credentials:
        flow = flow_from_clientsecrets(filename=CLIENT_SECRETS,
                                       scope=" ".join(SCOPES))

        credentials = run_flow(flow=flow,
                               storage=storage,
                               flags=args,
                               http=http)

    return credentials


def safeint(i):
    if i == "" or None:
        return 0
    else:
        return int(i)

def sanitize_row(d):
    # properly translate to boolean.
    d['plan.isCommitmentPlan'] = (d.get('plan.isCommitmentPlan') is "TRUE")
    return d


def sanity_check(d):
    logging.info("Performing sanity check on domain (%s)..." % d['customerDomain'])

    domain = d.get('customerDomain')

    for field in REQUIRED_FIELDS:
        if d.get(field) is None:
            logging.error("%s: %s must have a value" % (domain, field))

    # validate planNames
    planName = d.get('plan.planName')
    if planName not in VALID_PLANNAMES:
        logging.error("%s: %s is not a valid plan.planName" %
                      (domain, planName))

    # validate SKU
    sku = d.get('skuId')
    if sku not in VALID_SKUS:
        logging.error('%s: "%s" is not a valid sku' % (domain, sku))

    # validate RenewalTypes
    renewalType = d.get('renewalSettings.renewalType')
    if renewalType not in VALID_RENEWAL_TYPES:
        logging.error("%s: '%s' is not a valid renewal type" % (domain, renewalType))

    # check commitment for sanity.
    commitmentPlan = d.get('plan.isCommitmentPlan')
    startTime = safeint(d.get('plan.commitmentInterval.startTime'))
    endTime = safeint(d.get('plan.commitmentInterval.endTime'))
    if commitmentPlan == "TRUE":
        if startTime == 0:
            logging.error("%s: %s a startTime is required" % (domain, startTime))

        if endTime == 0:
            logging.error("%s: %s an endTime is required" % (domain, endTime))

        if startTime > endTime:
            logging.error("%s: The commitment must end after it starts" % domain)

    # check seat count for sanity
    seats = safeint(d.get('seats.numberOfSeats'))
    maxSeats = safeint(d.get('seats.maximumNumberOfSeats'))
    if 0 in [seats, maxSeats]:
        logging.error("%s: Seats cannot be 0" % domain)
    if seats > maxSeats:
        logging.error("%s: Seats cannot be larger than max seats")


def main(args):
    domains = csv.DictReader(open(args.in_file, 'rb'))
    domains = [sanitize_row(d) for d in domains if len(d.get('customerDomain')) > 0]

    args.apply = True
    if not args.apply:
        print "=== DRY RUN MODE -- NOT APPLYING CHANGES! ==="

    for d in domains:
        # sanity check will log any weird errors.
        sanity_check(d)

    if not args.apply:
        exit("=== DRY RUN MODE -- NOT APPLYING CHANGES! ===")

    credentials = get_credentials(args)
    credentials.authorize(http)
    service = build(serviceName="reseller",
                    version=RESELLER_API_VERSION,
                    http=http)

    for d in domains:
        domain = d['customerDomain']
        time.sleep(THROTTLE_SLEEP)

        # test to see if a customer exists in Google.
        # if the customer does not exist anywhere, then skip this entry
        try:
            service.customers().get(
                customerId=d['customerDomain']).execute(num_retries=NUM_RETRIES)
        except Exception, e:
            logging.error("%s: Customer doesn't exist yet, skipping transfer")
            logging.exception(e)
            continue

        print "Trying to create subscription..."
        try:
            # Add a Google Apps subscription record.
            response = service.subscriptions().insert(
                customerId=d['customerDomain'],
                trace=None,
                customerAuthToken=d['customerAuthToken'],
                body={
                    'customerId': d['customerDomain'],
                    'subscriptionId': d['subscriptionId'],
                    'skuId': d['skuId'],
                    'plan': {
                        'planName': d['plan.planName'],
                        'isCommitmentPlan': bool(d['plan.isCommitmentPlan']),
                        'commitmentInterval': {
                            'startTime':
                                safeint(d['plan.commitmentInterval.startTime']),
                            'endTime':
                                safeint(d['plan.commitmentInterval.endTime'])
                        }
                    },
                    'seats': {
                        'numberOfSeats':
                            safeint(d['seats.numberOfSeats']),
                        'maximumNumberOfSeats':
                            safeint(d['seats.maximumNumberOfSeats'])
                    },
                    'renewalSettings': {
                        'renewalType': d['renewalSettings.renewalType']
                    },
                    'purchaseOrderId': d['purchaseOrderId']
                }).execute(num_retries=NUM_RETRIES)
        except Exception, e:
            logging.error("%s: Error performing transfer" % domain)
            logging.exception(e)

        time.sleep(THROTTLE_SLEEP)

if __name__ == "__main__":

    parser = ArgumentParser(parents=[run_parser])
    parser.add_argument("--in_file")
    parser.add_argument("--apply", default=False, action="store_true")

    args = parser.parse_args()

    main(args)