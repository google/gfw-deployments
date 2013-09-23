#!/usr/bin/python
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the Licens

"""Dumps high level inventory of docs across a domain.

   Prerequisites for domain:
     - Admin account for the domain (user/pass)
     - OAuth Enabled Consumer Key - As an admin, in the control panel,
       go to "Advanced Tools" -> "Manage OAuth domain key" page.
       Click the "Enable this consumer key" setting.  For more information:
       http://www.google.com/support/a/bin/answer.py?hl=en&answer=162106
     - Configure client API access - As an admin, go to the control panel,
       "Advanced Tools" -> "Manage third party OAuth Client access" and
       in the "Client Name" field add your domain and in the "One or More API Scopes"
       field add: "http://docs.google.com/feeds/" and click Authorize.


   Prints a count of documents by document type.

   If desirable, the --times flag can be provided to
   create a CSV of document metadata for all
   documents domain wide.

   The CSV contains these fields only:
     - document type (document, spreadsheet, or presentation)
     - last updated timestamp
     - last published timestamp
     - last viewed timestamp

   and is written in the directory where the program is run
   with the name domain_docs_times_<timestamp>.csv

   For information on how to run, run with the help parameter:
     get_domain_doc_inventory.py -h
"""

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import csv
import datetime
import gdata.apps.service as apps_service
import gdata.docs.client
import gdata.gauth
import sys

from operator import itemgetter
from optparse import OptionParser


def ParseInputs():
  """Checks that required parameters are present."""

  usage = """usage: %prog -k <consumer_key> -s <consumer_secret>\n"""
  parser = OptionParser()
  parser.add_option("-k", dest="consumer_key", help="OAuth Consumer Key")
  parser.add_option("-s", dest="consumer_secret", help="OAuth Consumer Secret")
  parser.add_option("-u", dest="admin_user", help="admin user")
  parser.add_option("-p", dest="admin_pass", help="admin pass")
  parser.add_option("-d", dest="domain", help="domain")
  parser.add_option("--by_user", action="store_true", dest="by_user",
                    help="If specified, will print a count of docs by user.")
  parser.add_option("--times", action="store_true", dest="times",
                    help="""If specified, will dump a csv with the timestamps
                            of last update, last publish, and last view""")

  (options, args) = parser.parse_args()

  invalid_args = False
  if options.consumer_key is None:
    print "-k (consumer_key) is required"
    invalid_args = True
  if options.consumer_secret is None:
    print "-s (consumer_secret) is required"
    invalid_args = True
  if options.admin_user is None:
    print "-u (admin_user) is required"
    invalid_args = True
  if options.admin_pass is None:
    print "-p (admin_pass) is required"
    invalid_args = True
  if options.domain is None:
    print "-d (domain) is required"
    invalid_args = True

  if invalid_args:
    sys.exit(4)

  return options


def GetClient(requestor_id, consumer_secret, consumer_key):
  client = gdata.docs.client.DocsClient(source='docs_meta-v1')
  client.auth_token = gdata.gauth.TwoLeggedOAuthHmacToken(
      consumer_key, consumer_secret, requestor_id)
  return client


def GetAllUsers(admin_user, admin_pass, domain):
  """Returns a list of all provisioned users for a domain."""

  users = []
  conn = apps_service.AppsService(email=admin_user,
                                  domain=domain,
                                  password=admin_pass)
  conn.ProgrammaticLogin()

  user_feed = conn.RetrieveAllUsers()
  for user_entry in user_feed.entry:
    if user_entry.login.suspended != 'true':
      users.append(user_entry.login.user_name.lower())
    else:
      print "Skipping suspended user [%s]" % user_entry.login.user_name.lower()
  return users


def GetUserDocsFeed(requestor_id, consumer_secret, consumer_key):
  """Returns a document feed for a given user."""

  client = GetClient(requestor_id, consumer_secret, consumer_key)
  feed = client.GetEverything()
  return feed


def GetTimeStamp():
  now = datetime.datetime.now()
  return now.strftime("%Y%m%d%H%M%S")


def FormatTime(time):
  return time.replace('T', ' ').replace('Z', '')


def main():

  # Parse input params
  options = ParseInputs()

  # Doc count dict
  docs = {}

  # Total Docs counter
  counter = 0

  # User dict
  by_user = {}
  user_count = {}

  if options.times:
    # Open file for CSV write
    csv_file_name = 'domain_docs_times_%s.csv' % GetTimeStamp()
    csv_writer = csv.writer(open(csv_file_name, 'wb'), delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(["DocType", "LastUpdated",
                         "LastPublished", "LastViewed"])

  # For each user dump doc metadata
  for user in GetAllUsers(options.admin_user, options.admin_pass,
                          options.domain):

    print "Getting doc feed for user: %s" % user
    try:
      for doc in GetUserDocsFeed("%s@%s" % (user, options.domain),
                                 options.consumer_secret,
                                 options.consumer_key):
        for category in doc.category:

          # TODO(mdauphinee): Find an improvement for this check
          if category.label.lower() == 'viewed':
            continue

          #print "\n%s\n" % doc
          #print dir(doc)
          authors = []
          full_username = "%s@%s" % (user, options.domain)
          for a in doc.author:
            #print "Author: %s" % a.email.text
            authors.append(a.email.text)
          #print "User: %s@%s" % (user, options.domain)

          # Exclude docs not owned by user
          if full_username not in authors:
            continue

          counter += 1

          # Increment the count dict by type
          if category.label in docs:
            docs[category.label] += 1
          else:
            docs[category.label] = 1

          if options.times:
            elem = [category.label.lower(),
                    FormatTime(doc.updated.text),
                    FormatTime(doc.published.text),
                    FormatTime(doc.last_viewed.text)]
            csv_writer.writerow(elem)

          if options.by_user:
            if user in by_user:
              if category.label in by_user[user]:
                by_user[user][category.label] += 1
              else:
                by_user[user][category.label] = 1
            else:
              by_user[user] = {category.label: 1}

            if user in user_count:
              user_count[user] += 1
            else:
              user_count[user] = 1
    except Exception, e:
      print "Exception in pulling data for user: %s" % str(e)

  print "\nTotal Docs: %d" % counter


  if options.times:
    print "\nCSV filename: %s" % csv_file_name

  if options.by_user:
    print "\nDocuments by user"
    sorted_list = sorted(by_user.items())
    for u in sorted_list:
      print u

    print "\nDocument Frequency by Owner"
    count_items = user_count.items()
    count_items.sort(key = itemgetter(1), reverse=True)
    for u in count_items:
      print "%s,%s" % u

  print "\nDocs Totals:"
  print docs


if __name__ == '__main__':
  main()
