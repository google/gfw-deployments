#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.

"""Prints out contact data using oAuth 1.0 for domain-wide delegation.

   ###########################################################################
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
   ###########################################################################

   Usage: export_contacts.py [options]

   Options:
     -h, --help            show this help message and exit
     --user=OAUTH_REQUESTOR_ID
                           The target user to list contacts.
     --key=OAUTH_CONSUMER_KEY
                           The OAuth consumer key
     --secret=OAUTH_CONSUMER_SECRET
                           The The OAuth consumer secret.

"""
__author__ = 'hartung@google.com (Justin Hartung)'

from optparse import OptionParser
import sys

import gdata.auth
import gdata.contacts.client
import gdata.contacts.data


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  parser = OptionParser()
  parser.add_option('--user', dest='oauth_requestor_id',
                    help='The target user/requestor_id to list contacts.')
  parser.add_option('--key', dest='oauth_consumer_key',
                    help='The OAuth consumer key')
  parser.add_option('--secret', dest='oauth_consumer_secret',
                    help='The The OAuth consumer secret.')

  (options, args) = parser.parse_args()
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))

  invalid_args = False
  if options.oauth_consumer_key is None:
    print '--key (consumer_key) is required'
    invalid_args = True
  if options.oauth_consumer_secret is None:
    print '--secret (consumer_secret) is required'
    invalid_args = True
  if options.oauth_requestor_id is None:
    print '--user (target user/requestor_id) is required'
    invalid_args = True

  if invalid_args:
    sys.exit(4)

  return options


def GetConnection(options):
  """Opens a connection to Google APIs using the provided parameters."""

  oauth_consumer_key = options.oauth_consumer_key
  oauth_consumer_secret = options.oauth_consumer_secret
  requestor_id = options.oauth_requestor_id

  two_legged_oauth_token = gdata.gauth.TwoLeggedOAuthHmacToken(
      oauth_consumer_key,
      oauth_consumer_secret,
      requestor_id)
  gd_client = gdata.contacts.client.ContactsClient(source='ContactsExporter')
  gd_client.auth_token = two_legged_oauth_token
  gd_client.ssl = True

  return gd_client


def PrintAllContacts(gd_client, user):
  """Print out all contacts for a given user."""

  # Loop through results as long as they return == max-results,
  #      then increase start-index and repeat.
  has_more = True
  i_loop = 1  # Keep track of loop number
  i_size = 5  # Max number of results for each loop
  while has_more:
    starting_count = i_size*(i_loop-1)  # Starting number of first returned item
    uri = ('https://www.google.com/m8/feeds/contacts/%s/full?'
           'max-results=%d&start-index=%d' % (user, i_size, starting_count+1))
    feed = gd_client.GetContacts(uri=uri)

    i_recordnumber = 0  # Keep track of how may objects returned
    for i, entry in enumerate(feed.entry):
      i_recordnumber += 1
      if entry.name and entry.name.full_name:
        print '\n%s %s' % (starting_count+i+1, entry.name.full_name.text)
      else:
        print '\n%s %s' % (starting_count+i+1, entry.id.text)

      if entry.content:
        print '    %s' % (entry.content.text)
      # Display the primary email address for the contact.
      for email in entry.email:
        if email.primary and email.primary == 'true':
          print '    %s' % (email.address)
      # Show the contact groups that this contact is a member of.
      for group in entry.group_membership_info:
        print '    Member of group: %s' % (group.href)
      # Display extended properties.
      for extended_property in entry.extended_property:
        if extended_property.value:
          value = extended_property.value
        else:
          value = extended_property.GetXmlBlob()
        print '    Extended Property - %s: %s' % (extended_property.name, value)

    # If we have exactly the max returned, then loop and get some more results
    if i_recordnumber == i_size:
      has_more = True
    else:
      has_more = False
    i_loop += 1


def main():
  options = ParseInputs()
  gd_client = GetConnection(options)
  PrintAllContacts(gd_client, options.oauth_requestor_id)

if __name__ == '__main__':
  main()


