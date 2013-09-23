#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Dumps users and their timezones to CSV.

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


Usage: export_user_tz_to_csv.py [options]

Options:
  -h, --help            show this help message and exit
  -d DOMAIN             The domain name in which to add groups.
  -u ADMIN_USER         The admin user to use for authentication.
  -p ADMIN_PASS         The admin user's password
  -o USERS_OUTPUT_FILENAME
                        The output file to write the user data to.
  -k CONSUMER_KEY       The consumer key.
  -s CONSUMER_SECRET    The consumer secret.

"""

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import csv
from optparse import OptionParser
import re
import sys
import gdata.gauth
import gdata.apps.service as apps_service
import gdata.calendar.service as cal_service


def GetCalendarServiceConnection(username, consumer_key, consumer_secret):
    """Method to create our Connection."""

    sig_method = gdata.auth.OAuthSignatureMethod.HMAC_SHA1
    conn = gdata.calendar.service.CalendarService(source='timezone_update')
    conn.SetOAuthInputParameters(signature_method=sig_method,
                                 consumer_key=consumer_key,
                                 consumer_secret=consumer_secret,
                                 two_legged_oauth=True,
                                 requestor_id=username)
    return conn



def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  parser = OptionParser()
  parser.add_option('-d', dest='domain',
                    help='The domain name in which to add groups.')
  parser.add_option('-u', dest='admin_user',
                    help='The admin user to use for authentication.')
  parser.add_option('-p', dest='admin_pass',
                    help="The admin user's password")
  parser.add_option('-o', dest='users_output_filename', default='users.csv',
                    help='The output file to write the user data to.')
  parser.add_option('-k', dest='consumer_key',
                    help="""The consumer key.""")
  parser.add_option('-s', dest='consumer_secret',
                    help="""The consumer secret.""")


  (options, args) = parser.parse_args()
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))

  if options.domain is None:
    print '-d (domain) is required'
    sys.exit(1)
  if options.admin_user is None:
    print '-u (admin user) is required'
    sys.exit(1)
  if options.admin_pass is None:
    print '-p (admin password) is required'
    sys.exit(1)
  if options.consumer_key is None:
    print '-k (consumer_key) is required'
    sys.exit(1)
  if options.consumer_secret is None:
    print '-s (consumer_secret) is required'
    sys.exit(1)

  return options


def GetConnection(options):
  service = apps_service.AppsService(email=options.admin_user,
                                     domain=options.domain,
                                     password=options.admin_pass)
  service.ProgrammaticLogin()
  return service


def InitializeOutputFile(user_filename):
  """Creates file with headers for user data."""

  # Create groups output file
  users_file = csv.DictWriter(open(user_filename, 'w'),
                              fieldnames=['email address',
                                          'first name',
                                          'last name',
                                          'tz'],
                              delimiter=',')
  users_file.writerow({'email address': 'email address',
                       'first name': 'first name',
                       'last name': 'last name',
                       'tz': 'tz'})

  return users_file

def ExistingTimezone(connection, username):
    """Method to check to see if the Calendar timezone is correct."""

    feed = connection.GetOwnCalendarsFeed()

    for cal in feed.entry:
      # TODO(mdauphinee): Confirm that this is the best way to grab the primary
      #                   cal
      if cal.title.text == username:
        return cal.timezone.value


def main():

  options = ParseInputs()

  user_f = InitializeOutputFile(options.users_output_filename)

  connection = GetConnection(options)
  user_feed = connection.RetrieveAllUsers()

  user_counter = 0
  for user_entry in user_feed.entry:

    # Skip suspended users
    if user_entry.login.suspended == 'true':
      continue

    username = '%s@%s' % (user_entry.login.user_name,
                          options.domain)
    print "Requesting tz for %s" % username
    conn = GetCalendarServiceConnection(username, options.consumer_key, options.consumer_secret)
    tz = ExistingTimezone(conn, username)

    #print user_entry
    user_counter += 1
    user_f.writerow({'email address': '%s@%s' % (user_entry.login.user_name,
                                                 options.domain),
                     'first name': user_entry.name.given_name,
                     'last name': user_entry.name.family_name,
                     'tz': tz})


if __name__ == '__main__':
  main()
