#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Copyright (C) 2011 Google Inc.
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

"""


__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import csv
import datetime
import logging
from optparse import OptionParser
import sys
import time

import gdata.calendar
import gdata.calendar.client
import gdata.calendar.service
import gdata.gauth

def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""
  usage = """TBD"""
  parser = OptionParser(usage=usage)
  parser.add_option('-a', dest='oauth_requestor_id',
                    help="""The OAuth Requestor email address.""")
  parser.add_option('-k', dest='consumer_key',
                    help="""The consumer key.""")
  parser.add_option('-s', dest='consumer_secret',
                    help="""The consumer secret.""")
  parser.add_option('-r', dest='resource_address',
                    help="""Resource's email address.""")
  parser.add_option('-o', dest='old_resource_address',
                    help="""Old resource's email address.""")
  parser.add_option('-c', dest='organizer_calendar',
                    help="""Email address of organizer.""")
  parser.add_option('-w', dest='where',
                    help="""Where (Text name of resource).""")

  (options, args) = parser.parse_args()

  # series of if's to check our flags
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))
  if not options:
    parser.print_help()
    sys.exit(1)
  if options.oauth_requestor_id is None:
    print '-a (oauth_requestor_id) is required'
    sys.exit(1)
  if options.consumer_key is None:
    print '-k (consumer_key) is required'
    sys.exit(1)
  if options.consumer_secret is None:
    print '-s (consumer_secret) is required'
    sys.exit(1)
  if options.resource_address is None:
    print '-r (resource_address) is required'
    sys.exit(1)
  if options.old_resource_address is None:
    print '-o (old_resource_address) is required'
  if options.organizer_calendar is None:
    print '-c (organizer) is required'
    sys.exit(1)
  if options.where is None:
    print '-w (where) is required'
    sys.exit(1)


  return options


def GetTimeStamp():
  now = datetime.datetime.now()
  return now.strftime('%Y%m%d%H%M%S')


def GetCalendarServiceConnection(source_name, two_lo, key, secret, sig_method, username):
  """Method to create our Connection."""

  conn = gdata.calendar.service.CalendarService(source="cal_check")
  conn.SetOAuthInputParameters(signature_method=sig_method,
                               consumer_key=key,
                               consumer_secret=secret,
                               two_legged_oauth=two_lo,
                               requestor_id=username)

  return conn


def main():

  options = ParseInputs()

  start = time.time()

  # Set up logging
  log_filename = ('swap_resources_%s.log' %
                  (datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  logging.info("Looking for events on [%s]'s calendar", options.resource_address)

  cal_conn = GetCalendarServiceConnection("swap_resources", True, options.consumer_key,
                                          options.consumer_secret, gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                                          options.oauth_requestor_id)

  feed = cal_conn.GetCalendarEventFeed(uri='/calendar/feeds/' + options.organizer_calendar + '/private/full')

  status = gdata.calendar.AttendeeStatus()
  status.value = 'INVITED'
  att_type = gdata.calendar.AttendeeType()
  att_type.value = 'REQUIRED'

  for i, an_event in enumerate(feed.entry):
    needs_to_be_updated = False
    new_who = []
    for p in an_event.who:
      # If we find the old resource
      if p.email == options.old_resource_address:
        logging.info("Found event with old resource with title [%s]", an_event.title.text)
        new_who.append(gdata.calendar.Who(email=options.resource_address,
                                          attendee_status=status,
                                          attendee_type=att_type))
        needs_to_be_updated = True
      else:
        new_who.append(p)

    if needs_to_be_updated:
      # Swap in list of attendees that excludes old resource and includes new
      an_event.who = new_who

      # TODO(mdauphinee) Look up the text of the resource name versus requiring
      #                  it be passed in.
      # Also update the "Where" text on the event
      new_where = []
      new_where.append(gdata.calendar.Where(value_string=options.where))
      an_event.where = new_where

      # Update the event
      new_event = cal_conn.UpdateEvent(an_event.GetEditLink().href, an_event)
      logging.info("Updated event")

if __name__ == '__main__':
  main()
