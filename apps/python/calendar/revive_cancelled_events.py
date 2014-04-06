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

from argparse import ArgumentParser

from apiclient.discovery import build
from apiclient.http import HttpError
from apiclient.http import BatchHttpRequest
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
    'https://www.googleapis.com/auth/calendar'
]

AUTH_STORAGE_FILE = "auth_cal.dat"
CLIENT_SECRETS = "client_secrets.json"

BATCH_SIZE = 50

http = httplib2.Http()

def chunks(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def get_credentials(args):
    storage = Storage(AUTH_STORAGE_FILE)

    flow = flow_from_clientsecrets(filename=CLIENT_SECRETS,
                                   scope=SCOPES)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = run_flow(flow=flow,
                               storage=storage,
                               flags=args,
                               http=http)
        storage.put(credentials)
    return credentials

def main(args):


    if not args.apply:
      print "=" * 60
      print "DRY RUN MODE"
      print "=" * 60

    credentials = get_credentials(args)
    credentials.authorize(http)

    calendar = build('calendar', 'v3', http=http)

    rows = csv.reader(open(args.input, 'r'))

    for user, in rows:
      calendarId = user
      all_events = []
      pageToken = None

      while True:
        events = calendar.events().list(
          calendarId=user,
          maxResults=1000,
          pageToken=pageToken,
          showDeleted=True,
          fields="items(id,status,extendedProperties),nextPageToken").execute()

        # dump this round of events in a master array.
        all_events.extend(events['items'])

        pageToken = events.get('nextPageToken')
        if pageToken is None:
          break

      # filter for cancelled events, since it can't be done via the api.
      cancelled_events = [e for e in all_events if e['status'] == "cancelled"]

      print "User %s has %d tombstoned events out of %d" % \
        (calendarId, len(cancelled_events), len(all_events))

      # optionally remove previously revived events..
      if not args.force:
        cancelled_events = [e for e in cancelled_events if e['extendedProperties']['shared'].get('_revived') is None]

      batches = chunks(cancelled_events, BATCH_SIZE)

      print "Reviving %d events.." % len(cancelled_events)

      if args.apply:
        for events in batches:
          print "Batch..."
          batch = BatchHttpRequest()
          for event in events:
            batch.add(calendar.events().patch(
              calendarId=calendarId,
              eventId=event['id'],
              body={
                'status': 'tentative',
                'extendedProperties': {
                  'shared': {
                    '_revived': True
                  }
                }
              }))
          batch.execute(http=http)




if __name__ == "__main__":
    parser = ArgumentParser(parents=[run_parser])
    parser.add_argument("--input")
    parser.add_argument("--force", action="store_true", default=False)
    parser.add_argument("--apply", action="store_true", default=False)
    args = parser.parse_args()
    main(args)