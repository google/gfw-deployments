#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.

"""Utility script to remove all events from user's calendars.

Copyright (C) 2012 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

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
THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR ITS
DERIVATIVES.
###########################################################################

Description:
  The following script utilizes the V3 Google Calendar API in order to
  clear all events on the primary calendar for each user in given in an
  input file.

  NOTE: The scope "https://www.googleapis.com/auth/calendar" should be added
        to the Control Panel under the "Manage third party OAuth Client access"
        section of the Control Panel's Advanced tools with the client name
        of the domain name.

Usage: clear_user_calendars.py
          -k <consumer key> -s <consumer secret>
          -u <admin user> -d <developer_key>
          -f <input_file_of_users>

Options:
  -h, --help          show this help message and exit
  -k CONSUMER_KEY     The 2LO consumer key.
  -s CONSUMER_SECRET  The 2LO consumer secret.
  -u ADMIN_USER       Admin user e.g. user@domain.com.
  -d DEVELOPER_KEY    Developer Key from API Console.
  -f USER_INPUT_FILE  Input file containing list of users
                      to clear events.

"""

__author__ = 'jstanway@google.com (Jeff Stanway)'


import csv
import datetime
import logging
from optparse import OptionParser
import sys
from apiclient import oauth
from apiclient.discovery import build
import httplib2


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  usage = """%prog -k <consumer key> -s <consumer secret> -u <admin user>
              -f <input_file_of_users>"""
  parser = OptionParser(usage=usage)
  parser.add_option('-k', dest='consumer_key',
                    help='The 2LO consumer key.')
  parser.add_option('-s', dest='consumer_secret',
                    help='The 2LO consumer secret.')
  parser.add_option('-u', dest='admin_user',
                    help='Admin user e.g. user@domain.com.')
  parser.add_option('-d', dest='developer_key',
                    help='Developer Key from API Console.')
  parser.add_option('-f', dest='user_input_file',
                    help="""Input file containing list of users'
                            email addresses for which we will
                            clear events.""")
  (options, args) = parser.parse_args()

  invalid_args = False
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))
  if not options:
    parser.print_help()
    invalid_args = True
  if options.consumer_key is None:
    print '-k (consumer_key) is required'
    invalid_args = True
  if options.consumer_secret is None:
    print '-s (consumer_secret) is required'
    invalid_args = True
  if options.admin_user is None:
    print '-u (admin_user) is required'
    invalid_args = True
  if options.developer_key is None:
    print '-d (developer_key) is required'
    invalid_args = True
  if options.user_input_file is None:
    print '-f (user_input_file) is required'
    invalid_args = True

  if invalid_args:
    sys.exit(1)

  return options


def main(argv):

  options = ParseInputs()

  # Set up logging
  log_filename = ('clear_user_calendars_%s.log' %
                  (datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  credentials = oauth.TwoLeggedOAuthCredentials(
      consumer_key=options.consumer_key,
      consumer_secret=options.consumer_secret,
      user_agent='Python-EDT-Cal-Clear/1.0')
  credentials.setrequestor(options.admin_user)

  http = httplib2.Http()
  http = credentials.authorize(http)

  # Build a service object for interacting with the API. Visit
  # the Google APIs Console
  # to get a developerKey for your own application.
  service = build(serviceName='calendar',
                  version='v3',
                  http=http,
                  developerKey=options.developer_key)

  reader = csv.reader(open(options.user_input_file, 'rb'))
  for row in reader:
    username = row[0]
    credentials.setrequestor(username)
    logging.info('Clearing calendar for [%s]', username)
    try:
      service.calendars().clear(calendarId=username, body='').execute()
      logging.info('Done clearing calendar for [%s]', username)
    except oauth.CredentialsInvalidError, e:
      logging.error('Authentication Error: [%s]', str(e))


if __name__ == '__main__':
  main(sys.argv)
