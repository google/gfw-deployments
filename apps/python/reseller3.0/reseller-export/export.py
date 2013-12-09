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
    Provides the ability to export a record of all subscriptions for a reseller.

    Setup:
        - Create an OAuth2 Project and enable the Reseller API
        - Create a client id for "installed applications"
        - Download the client_secrets.json file and place it in the same dir.
        - Run the script to authorize the script.
        - The script will need to be authorized as a Domain Administrator
        - Credentials are stored permanently in an 'auth.dat' file.

    Usage:
        - Run the script "python import.py --out_file out.csv

"""
from argparse import ArgumentParser

from apiclient.discovery import build

import collections
import csv

import httplib2
import logging

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

http = httplib2.Http()

# shamelessly borrowed from:
# http://stackoverflow.com/questions/6027558/
# flatten-nested-python-dictionaries-compressing-keys
def flatten(d, parent_key='', sep="."):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)

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


def main(args):
    credentials = get_credentials(args)
    credentials.authorize(http)
    service = build(serviceName="reseller",
                    version=RESELLER_API_VERSION,
                    http=http)

    writer = csv.DictWriter(
        open(args.out_file, 'wb'),
        fieldnames=[
            'customerId',
            'subscriptionId',
            'skuId',
            'creationTime',
            'plan.planName',
            'plan.isCommitmentPlan',
            'plan.commitmentInterval.startTime',
            'plan.commitmentInterval.endTime',
            'seats.numberOfSeats',
            'seats.maximumNumberOfSeats',
            'trialSettings.isInTrial',
            'trialSettings.trialEndTime',
            'renewalSettings.renewalType',
            'transferInfo.transferabilityExpirationTime',
            'transferInfo.minimumTransferableSeats',
            'purchaseOrderId',
            'status',
            'resourceUiUrl'
        ])

    writer.writeheader()
    pageToken = ""
    while pageToken is not None:
        response = service.subscriptions().list(pageToken=pageToken).\
            execute(num_retries=NUM_RETRIES)
        
        pageToken = response.get('nextPageToken')

        for subscription in response['subscriptions']:
            data = flatten(subscription)
            writer.extrasaction = "raise"
            try:
                writer.writerow(data)
            except ValueError, e:
                # log it as a warning, but continue..
                logging.warning(e)
                writer.extrasaction = "ignore"
                writer.writerow(data)



if __name__ == "__main__":

    parser = ArgumentParser(parents=[run_parser])
    parser.add_argument("--out_file")

    args = parser.parse_args()

    main(args)