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
    Allocates an alias on an alternate domain name for all users on a
    given domain name.

    This is useful for establishing "domain aliases" on secondary domains.

    Setup:
     - Create an OAuth2 Project and enable the Admin SDK
     - Create a client id for "installed applications"
     - Download the client_secrets.json file and place it in the same dir.
     - Run the script for the first time to authorize the script.
       - The script will need to be authorized as a Domain Administrator
     - Credentials are stored permanently in an 'auth.dat' file.

    Example:
     python main.py --domain acmecorp.com --shadow g.acmecorp.com
     (all users on acmecorp.com receive a g.acmecorp.com alias)
     (e.g. bob@g.acmecorp.com -> bob@acmecorp.com)
"""

__author__ = 'richieforeman@google.com (Richie Foreman)'

from argparse import ArgumentParser
import httplib2
from Queue import Queue
import threading

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
try:
    # the documentation says to import his way...
    from oauth2client.tools import run_parser
except ImportError:
    # .. but it doesn't work, so fall back to this.
    from oauth2client.tools import argparser as run_parser

SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/admin.directory.user.alias'
]

AUTH_STORAGE_FILE = "auth.dat"
CLIENT_SECRETS = "client_secrets.json"
THREADS = 25

http = httplib2.Http()


class UserShadowNickThread(threading.Thread):
    '''
    Thread class that receives a queue of users
    and applies a shadow nickname to each
    '''
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
            if not user['suspended']:
                queue.put(user)

        nextToken = response.get("nextPageToken", None)

    print "Waiting for all threads to rejoin parent..."
    queue.join()
    print "All threads rejoined parent. Done!"


if __name__ == "__main__":
    parser = ArgumentParser(parents=[run_parser])
    parser.add_argument("--domain")
    parser.add_argument("--shadow")
    main(parser.parse_args())