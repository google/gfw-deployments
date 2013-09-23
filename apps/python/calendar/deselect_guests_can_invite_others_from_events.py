#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Unchecks Guests can invite others for a user's events.

Copyright (C) 2011 Google Inc.
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

Usage: deselect_guests_can_invite_others_from_events.py -k <consumer key>
              -s <consumer secret> -u <admin user> -p <admin password>

Options:
  -h, --help          show this help message and exit
  -k CONSUMER_KEY     The consumer key.
  -s CONSUMER_SECRET  The consumer secret.
  -u CALENDAR_USER    The calendar user to change defaults on.
  -b BEGIN_DATE       Begin Date for calendar range query in YYYY-MM-DD
  -e END_DATE         End Date for calendar range query in YYYY-MM-DD

Example: ./deselect_guests_can_invite_others_from_events.py
           -k mdauphinee.info
           -s "laksdjf;lkajsdflkjsadflkj"
           -b 2011-01-01
           -e 2011-11-30
           -u administrator@mdauphinee.info
"""


__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import datetime
import logging
from optparse import OptionParser
import sys

import gdata.calendar
import gdata.calendar.service
import gdata.gauth


def GetCalendarServiceConnection(options, username):
  """Method to create our Connection."""

  sig_method = gdata.auth.OAuthSignatureMethod.HMAC_SHA1

  conn = gdata.calendar.service.CalendarService(source='uncheck_invite_others')
  conn.SetOAuthInputParameters(signature_method=sig_method,
                               consumer_key=options.consumer_key,
                               consumer_secret=options.consumer_secret,
                               two_legged_oauth=True,
                               requestor_id=username)
  return conn


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""
  usage = """%prog -k <consumer key> -s <consumer secret> -u <admin user> -p
              <admin password>"""
  parser = OptionParser(usage=usage)
  parser.add_option('-k', dest='consumer_key',
                    help='The consumer key.')
  parser.add_option('-s', dest='consumer_secret',
                    help='The consumer secret.')
  parser.add_option('-u', dest='calendar_user',
                    help='The calendar user to change defaults on.')
  parser.add_option('-b', dest='begin_date',
                    help='Begin Date for calendar range query in YYYY-MM-DD')
  parser.add_option('-e', dest='end_date',
                    help='End Date for calendar range query in YYYY-MM-DD')

  (options, args) = parser.parse_args()

  # series of if's to check our flags
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
  if options.calendar_user is None:
    print '-u (calendar_user) is required'
    invalid_args = True
  if options.begin_date is None:
    print '-b (begin_date) is required'
    invalid_args = True
  if options.end_date is None:
    print '-e (end_date) is required'
    invalid_args = True

  if invalid_args:
    sys.exit(1)

  return options


def GetTimeStamp():
  now = datetime.datetime.now()
  return now.strftime('%Y%m%d%H%M%S')


def main():

  options = ParseInputs()

  # Set up logging
  log_filename = ('find_edu_events_%s.log' %
                  (datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  logging.info("Searching [%s]'s calendar", options.calendar_user)
  conn = GetCalendarServiceConnection(options, options.calendar_user)
  query = gdata.calendar.service.CalendarEventQuery('default',
                                                    'private',
                                                    'full')
  query.start_min = options.begin_date
  query.start_max = options.end_date
  feed = conn.CalendarQuery(query)
  for an_event in feed.entry:
    if an_event.guests_can_invite_others.value == 'true':
      for a_when in an_event.when:
        for organizer in an_event.author:
          if options.calendar_user.lower() == organizer.name.text.lower():
            logging.info('Unchecking guests can invite others for [%s][%s][%s]',
                         a_when.start_time,
                         a_when.end_time,
                         an_event.title.text)
            an_event.guests_can_invite_others.value = 'false'
            try:
              new_event = conn.UpdateEvent(an_event.GetEditLink().href,
                                           an_event)
            except Exception, err:
              logging.error('\tException when processing update [%s]', str(err))
  logging.info("Completed [%s]'s calendar", options.calendar_user)


if __name__ == '__main__':
  main()
