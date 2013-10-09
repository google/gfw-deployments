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
    A simple example of connecting to the Cloud Directory API in Python
    and properly handling pagination.

    Note: All list calls within the Apiary APIs handle pagination the same,
    and this technique could be used in other places (drive, groups, etc)

    Setup:
     - Create an OAuth2 Project and enable the Admin SDK
     - Create a client id for "installed applications"
     - Download the client_secrets.json file and place it in the same dir.
     - Run the script for the first time to authorize the script.
       - The script will need to be authorized as a Domain Administrator
     - Credentials are stored permanently in an 'auth.dat' file.

    Usage:
    python directory.py --domain acmecorp.com

"""

__author__ = 'richieforeman@google.com (Richie Foreman)'

from argparse import ArgumentParser

from apiclient.discovery import build

import httplib2

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
try:
    from oauth2client.tools import run_parser
except ImportError:
    from oauth2client.tools import argparser as run_parser

SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user.readonly'
]

AUTH_STORAGE_FILE = 'auth.dat'
CLIENT_SECRETS = 'client_secrets.json'
http = httplib2.Http()


def get_credentials(args):
    storage = Storage(AUTH_STORAGE_FILE)
    credentials = storage.get()

    if not credentials:
        flow = flow_from_clientsecrets(filename=CLIENT_SECRETS,
                                       scope=SCOPES)

        credentials = run_flow(flow=flow,
                               storage=storage,
                               flags=args,
                               http=http)

    return credentials


def main(args):
    credentials = get_credentials(args)

    credentials.authorize(http)

    # build the directory service using the custom discovery url.
    service = build(serviceName="admin",
                    version="directory_v1",
                    http=http)

    users = []

    nextToken = ""
    while nextToken is not None:
        # loop thru pages of users and push them into a single users list.
        # Note: By utilizing the "num_retries" parameter,
        # the library can handle exponential backoff/retry on our behalf.
        # This is a feature of the client library, and can be used with ANY API!
        try:
            response = service.users().list(
                domain=args.domain,
                maxResults=100,
                showDeleted=False,
                orderBy="email",
                pageToken=nextToken,
                sortOrder="DESCENDING").execute(num_retries=5)
        except:
            print "The API threw an exception after several retry attempts!"
            exit()

        # push all of the users from this page into a list.
        users.extend(response['users'])

        # fetch the next page token.
        nextToken = response.get('nextPageToken', None)

    print "You have %d users in your domain" % len(users)

if __name__ == "__main__":
    parser = ArgumentParser(parents=[run_parser])
    parser.add_argument("--domain")
    main(parser.parse_args())