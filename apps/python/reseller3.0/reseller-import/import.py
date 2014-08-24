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
from apiclient.errors import HttpError

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
    'skuId',
    'plan.planName',
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
    "Google-Vault"
]
VALID_PLANNAMES = [
    'ANNUAL_MONTHLY_PAY',
    'ANNUAL_YEARLY_PAY',
    'FLEXIBLE',
    'TRIAL'
]
VALID_RENEWAL_TYPES = [
    'AUTO_RENEW_MONTHLY_PAY',
    'AUTO_RENEW_YEARLY_PAY',
    'RENEW_CURRENT_USERS_MONTHLY_PAY',
    'RENEW_CURRENT_USERS_YEARLY_PAY',
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

    # check seat count for sanity
    seats = safeint(d.get('seats.numberOfSeats'))
    maxSeats = safeint(d.get('seats.maximumNumberOfSeats'))
    if 0 in [seats, maxSeats]:
        logging.error("%s: Seats cannot be 0" % domain)
    if seats > maxSeats:
        logging.error("%s: Seats cannot be larger than max seats")

def create_customer(service, d):
    return service.customers().insert(
        customerAuthToken=d['customerAuthToken'],
        body={
            'customerDomain': d['customerDomain'],
            'customerId': d['customer.customerId'],
            'alternateEmail': d['customer.alternateEmail'],
            'phoneNumber': d['customer.phoneNumber'],
            'postalAddress': {
                'contactName': d['customer.contactName'],
                'organizationName': d['customer.organizationName'],
                'locality': d['customer.locality'],
                'region': d['customer.region'],
                'postalCode': d['customer.postalCode'],
                'countryCode': d['customer.countryCode'],
                'addressLine1': d['customer.addressLine1'],
                'addressLine2': d['customer.addressLine2'],
                'addressLine3': d['customer.addressLine3'],
            }
        }
    ).execute()

def create_subscription(service, d):
    # Add a Google Apps subscription record.
    while True:
        try:
            sub = service.subscriptions().insert(
                customerId=d['customerDomain'],
                trace=None,
                customerAuthToken=d['customerAuthToken'],
                body={
                    'customerId': d['customerDomain'],
                    'skuId': d['skuId'],
                    'plan': {
                        'planName': d['plan.planName'],
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
            break
        except HttpError, e:
            raise
        except Exception, e:
            logging.exception(e)
            time.sleep(5)




def main(args):
    domains = csv.DictReader(open(args.in_file, 'rb'))
    domains = [sanitize_row(d) for d in domains if len(d.get('customerDomain')) > 0]

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

        # test to see if a customer exists in Google.
        # if the customer does not exist anywhere, then skip this entry

        print "Trying to create subscription for domain (%s)..." % domain
        try:
            create_subscription(service=service, d=d)
        except HttpError, e:
            status = e.resp.status
            if status == 409:
                # pass, the customer has already been transferred.
                logging.warning("%s: Skipping customer (conflict)" % domain)
                pass
            elif status == 404:
                # they are in the super old billing system.
                # transfer customer from old billing
                try:
                    create_customer(service, d=d)
                except HttpError, ee:
                    logging.error("%s: Error when transferring "
                                  "customer from old billing" % domain)

                # transfer their Google Apps.
                try:
                    create_subscription(service, d=d)
                except HttpError, ee:
                    logging.error("%s: Error when transferring "
                                  "sub from old billing" % domain)
            elif status == 403:
                # probably suspended?
                logging.error("%s: Error performing transfer (403)" % domain)
                logging.exception(e)
            else:
                # an explosion has occured.
                logging.error("%s: Error performing transfer" % domain)
                logging.exception(e)

if __name__ == "__main__":

    parser = ArgumentParser(parents=[run_parser])
    parser.add_argument("--in_file")
    parser.add_argument("--apply", default=False, action="store_true")

    args = parser.parse_args()

    main(args)