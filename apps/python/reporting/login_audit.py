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
"""
    Provides the ability to export login audit records to CSV from the
    Reporting API. Searching is done on either IP address or Username
    (or both, offering a narrower result).

    Setup:
     - Create an OAuth2 Project and enable the Admin SDK and Reporting API
     - Create a client id for "installed applications"
     - Download the client_secrets.json file and place it in the same dir.
     - Run the script for the first time to authorize the script.
       - The script will need to be authorized as a Domain Administrator
     - Credentials are stored permanently in an 'auth.dat' file.

    Usage:
    python login_audit.py --userKey richie@acmecorp.com --ip 8.8.8.8 --outFile out.csv
    (fetches all logins from 8.8.8.8 for user richie@acmecorp.com)

    python login_audit.py --ip 8.8.8.8 --outFile out.csv
    (fetches all logins from 8.8.8.8 for any user)

    python login_audit.py --userKey richie@acmecorp.com --outFile out.csv
    (fetches all logins from any ip address for user richie@acmecorp.com )

"""
__author__ = 'richieforeman@google.com (Richie Foreman)'

from argparse import ArgumentParser

from apiclient.discovery import build

import csv

import httplib2

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
try:
    from oauth2client.tools import run_parser
except ImportError:
    from oauth2client.tools import argparser as run_parser

SCOPES = [
    'https://www.googleapis.com/auth/admin.reports.audit.readonly',
    'https://www.googleapis.com/auth/admin.reports.usage.readonly'
]

AUTH_STORAGE_FILE = "auth.dat"
CLIENT_SECRETS = 'client_secrets.json'

http = httplib2.Http()


def get_credentials(args):
    storage = Storage(AUTH_STORAGE_FILE)
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

    service = build(serviceName="admin",
                    version="reports_v1",
                    http=http)

    results = service.activities().list(
        applicationName="login",
        userKey=args.userKey,
        maxResults=1000).execute()

    writer = csv.DictWriter(f=file(args.outFile, 'wb'),
                            fieldnames=[
                                'actor.profileId',
                                'actor.email',
                                'ipAddress',
                                'uniqueQualifier',
                                'customerId',
                                'time',
                                'event.type',
                                'event.name',
                                'event.parameters'
                            ])
    writer.writeheader()

    for result in results['items']:
        for event in result['events']:
            parameters = []

            params = event.get('parameters')
            if params:
                for parameter in params:
                    # condense params
                    parameters.append("%s=%s" % \
                                      (parameter['name'], parameter['value']))


            entry = {
                'actor.profileId': result['actor']['profileId'],
                'actor.email': result['actor']['email'],
                'ipAddress': result.get('ipAddress'),
                'uniqueQualifier': result['id']['uniqueQualifier'],
                'customerId': result['id']['customerId'],
                'time': result['id']['time'],
                'event.type': event['type'],
                'event.name': event['name'],
                'event.parameters': ";".join(parameters)
            }

            writer.writerow(entry)

if __name__ == "__main__":

    parser = ArgumentParser(parents=[run_parser])
    parser.add_argument("--userKey", default="all")
    parser.add_argument("--ip", default=None)
    parser.add_argument("--outFile")

    args = parser.parse_args()

    main(args)
