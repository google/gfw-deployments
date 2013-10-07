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

import httplib2

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
try:
    from oauth2client.tools import run_parser
except ImportError:
    # hmm, seems like a bug in oauth2client to me.
    from oauth2client.tools import argparser as run_parser

from Queue import Queue

import threading

SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/admin.directory.user.alias'
]

AUTH_STORAGE_FILE = "auth.dat"
CLIENT_SECRETS = "client_secrets.json"
THREADS = 25

http = httplib2.Http()

def get_credentials(args):
    storage = Storage(AUTH_STORAGE_FILE)
    credentials = storage.get()

    if not credentials or credentials.invalid:
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

    # build the directory service
    service = build(serviceName="admin",
                    version="directory_v1",
                    http=http)

    # establish a queue which will drive our thread pool.
    queue = Queue(maxsize=THREADS*4)

    # prefork the threads.
    print "Forking %d Processor Threads... " % THREADS,

    for i in range(THREADS):
        print ".",
        UserShadowNickThread(queue=queue,
                             credentials=credentials,
                             args=args).start()
    print ".. Done!"

    # fetch user pages and push each user into the queue.
    nextToken = ""
    while nextToken is not None:
        response = service.users().list(domain=args.domain,
                                        pageToken=nextToken).execute()

        for user in response['users']:
            queue.put(user)

        nextToken = response.get("nextPageToken", None)

    print "Waiting for all threads to rejoin parent..."
    queue.join()
    print "All threads rejoined parent. Done!"


class UserShadowNickThread(threading.Thread):
    daemon = True

    q = None
    http = None
    credentials = None
    args = None

    def __init__(self, queue, credentials, args):
        threading.Thread.__init__(self)

        # httplib2 is not threadsafe (nor would we want it to be).
        # build a http connect for this thread.
        self.http = httplib2.Http()
        self.q = queue
        self.credentials = credentials
        self.args = args

        self.credentials.authorize(self.http)

    def run(self):
        while True:
            user = self.q.get()
            email = user['primaryEmail']

            # generate a flattened list of all email addresses for the user.
            all_emails = [u['address'].lower() for u in user['emails']]

            # calculate the shadow nick.
            shadow_nick = email.replace("@%s" % self.args.domain,
                                        "@%s" % self.args.shadow).lower()

            if shadow_nick not in all_emails:
                print "Creating shadow nick for user %s" % email
                service = build(serviceName="admin",
                                version="directory_v1",
                                http=self.http)

                # apiclient has baked in exponential backoff/retry
                try:
                    service.users().aliases().insert(
                        userKey=email,
                        body={
                            'primaryEmail': email,
                            'alias': shadow_nick
                        }).execute(num_retries=5)
                except:
                    print "Failed to create shadow nick for user %s" % email

            else:
                print "Skipping creation of shadow " \
                      "nick for user %s - Exists!" % email

            self.q.task_done()


if __name__ == "__main__":
    parser = ArgumentParser(parents=[run_parser])
    parser.add_argument("--domain")
    parser.add_argument("--shadow")
    main(parser.parse_args())