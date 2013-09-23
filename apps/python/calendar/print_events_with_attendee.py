#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.

"""Searches all users' primary calendars for events with specific attendees.

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

Given a specific file containing email addresses, this script searches the
primary calendar of all non-suspended users in the domain for events where
one of the email addresses in the input file is and attendee on the event.
For events that match, the events attributes are written to an output file
with these columns:
 - CalendarOwner
 - Organizer
 - Title
 - UID
 - StartTime
 - EndTime
 - PublishedTime
 - SyncEvent Attribute
 - IsRecurrence
 - Participants

Usage: print_events_with_attendee.py [options]

Options:
  -h, --help            show this help message and exit
  -k CONSUMER_KEY       The consumer key.
  -s CONSUMER_SECRET    The consumer secret.
  -u ADMIN_USER         Admin username.
  -p ADMIN_PASS         Admin user pass.
  -i ATTENDEE_INPUT_FILE
                        File with list of attendee addresses.
                        must have first line header of:
                        'email_address'
  -t THREADS            OPTIONAL: Number of threads to spawn,
                        max of 200.
  -r MAX_RETRY          OPTIONAL: Number of additional tries a thread will
                        make to perform the ACL before logging the error and
                        moving on.
  -f MAX_FAILURES       OPTIONAL: The maximum number of failures allowed
                        before the entire process is terminated.  Failure is
                        defined as a distinct user account that was not able
                        to be updated in the allowable retries.  For example,
                        if max_failures is set to 5 and max_retry is set to
                        3, if there are 6 user accounts for which we tried 4
                        times to update their ACL and failed, we will
                        terminate the process.
  --all                 If present, will pull the full cal feed
                        but limited to 9999 max events.
  --range               If present, expects --start and --end.
  --start=START         Start date. (YYYY-MM-DD)
  --end=END             End date. (YYYY-MM-DD)

Example invocation where:
 - it starts 10 threads,
 - searches a specific date range,
 - looks for events with one of the list of email addresses in the input
   file as an attendee

./print_events_with_attendee.py
   -k mdauphinee.info -s "ldslkfjkjjhkjlahsdfkljhF"
   -u administrator@mdauphinee.info -p mypass
   -i attendee_list.csv
   --range --start 2012-01-01 --end 2012-02-01
   -t 10
"""


__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import csv
import datetime
import logging
from optparse import OptionParser
import Queue
import sys
import threading
import time

import gdata.apps.service
import gdata.calendar
import gdata.calendar.service
import gdata.gauth

MAX_THREAD_VALUE = 200


class Instruction(object):
  """Class to hold instructions for the Queue."""

  def __init__(self, attendee_list, active_user):
    self.attendee_list = attendee_list
    self.active_user = active_user

  def GetAttendeeList(self):
    return self.attendee_list

  def GetActiveUser(self):
    return self.active_user


class ParticipantEvent(object):
  """Class to hold Event details."""

  def __init__(self, calendar_owner, organizer, title,
               uid, start_time, end_time, published_time,
               sync_event, recurrence, participants):
    self.calendar_owner = calendar_owner
    self.organizer = organizer
    self.title = title
    self.uid = uid
    self.start_time = start_time
    self.end_time = end_time
    self.published_time = published_time
    self.sync_event = sync_event
    self.recurrence = recurrence
    self.participants = participants

  def GetCalendarOwner(self):
    return self.calendar_owner

  def GetOrganizer(self):
    return self.organizer

  def GetTitle(self):
    return self.title

  def GetUid(self):
    return self.uid

  def GetStartTime(self):
    return self.start_time

  def GetEndTime(self):
    return self.end_time

  def GetPublishedTime(self):
    return self.published_time

  def GetSyncEvent(self):
    return self.sync_event

  def GetRecurrence(self):
    return self.recurrence

  def GetParticipants(self):
    return self.participants


class CalendarWorker(threading.Thread):
  """Threaded calendar worker."""

  def __init__(self, consumer_key, consumer_secret, work_queue, failure_queue,
               output_queue, max_retry, max_failures, options):
    """Creates a CalendarService and provides Oauth auth details to it."""

    threading.Thread.__init__(self)
    self.consumer_key = consumer_key
    self.consumer_secret = consumer_secret
    self.sig_method = gdata.auth.OAuthSignatureMethod.HMAC_SHA1
    self.work_queue = work_queue
    self.output_queue = output_queue
    self.failure_queue = failure_queue
    self.max_retry = max_retry
    self.max_failures = max_failures
    self.options = options

  def run(self):
    """Main worker that manages the jobs and applies changes for each user."""

    while True:

      # get task from queue
      task = self.work_queue.get()

      # retry counter
      retry_count = 0

      # process our users
      if self.failure_queue.qsize() <= self.max_failures:
        while retry_count <= self.max_retry:
          try:
            self._ProcessInstruction(task)
            break
          except Exception, err:
            logging.warning('Exception when processing [%s]: %s\n',
                            task.GetActiveUser(), str(err))
            retry_count += 1
            logging.info('Retrying user: [%s] (%s/%s)',
                         task.GetActiveUser(), retry_count, self.max_retry)
        else:
          logging.error('Max retries hit for [%s], skipping\n',
                        task.GetActiveUser())
          self.failure_queue.put(task)
      else:
        logging.error("""Max failures reached for user: [%s] (skipping all
                      subsequent entries).""", task.GetActiveUser())

      # signals to queue job is done
      self.work_queue.task_done()

  def _ProcessInstruction(self, task):
    logging.info('Reading the calendar of [%s]', task.GetActiveUser())
    connection = self._GetCalendarServiceConnection(task.GetActiveUser())

    if self.options.all:
      logging.info('Pulling full event feed.')
      max_results = 9999
      feed = connection.GetCalendarEventFeed(
          uri=('/calendar/feeds/default/private/full?max-results=%s'
               % max_results))
    else:

      # Date range
      logging.info('Pulling event feed from [%s] to [%s].',
                   self.options.start,
                   self.options.end)
      start_date = self.options.start
      end_date = self.options.end

      query = gdata.calendar.service.CalendarEventQuery('default',
                                                        'private',
                                                        'full')
      query.start_min = start_date
      query.start_max = end_date
      query.max_results = 9999
      feed = connection.CalendarQuery(query)

    for an_event in feed.entry:

      if an_event.recurrence:
        recurrence = 'Y'
      else:
        recurrence = 'N'

      #print an_event
      #print dir(an_event)
      #print an_event.sync_event
      #print an_event.recurrence
      #print an_event.recurrence_exception
      #print dir(an_event.sync_event)
      print_event = False
      for participant in an_event.who:
        for attendee in task.GetAttendeeList():
          if participant.email.lower() == attendee.lower():
            print_event = True  # Need to print this, but just once
          else:
            pass

      if print_event:
        for a in an_event.author:
          # Get list of participants
          participants = []
          for m in an_event.who:
            if m.email:
              participants.append(m.email)
            else:
              participants.append('n/a')
          for a_when in an_event.when:
            if an_event.published.text:
              publish_time = an_event.published.text
            else:
              publish_time = 'n/a'

            self.output_queue.put(ParticipantEvent(task.GetActiveUser(),
                                                   a.email.text,
                                                   an_event.title.text,
                                                   an_event.uid.value,
                                                   a_when.start_time,
                                                   a_when.end_time,
                                                   publish_time,
                                                   an_event.sync_event,
                                                   recurrence,
                                                   participants))

  def _GetCalendarServiceConnection(self, username):
    """Method to create our Connection."""

    conn = gdata.calendar.service.CalendarService(source='cal_check')
    conn.SetOAuthInputParameters(signature_method=self.sig_method,
                                 consumer_key=self.consumer_key,
                                 consumer_secret=self.consumer_secret,
                                 two_legged_oauth=True,
                                 requestor_id=username)
    return conn


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""
  parser = OptionParser()
  parser.add_option('-k', dest='consumer_key',
                    help="""The consumer key.""")
  parser.add_option('-s', dest='consumer_secret',
                    help="""The consumer secret.""")
  parser.add_option('-u', dest='admin_user',
                    help="""Admin username.""")
  parser.add_option('-p', dest='admin_pass',
                    help="""Admin user pass.""")
  parser.add_option('-i', dest='attendee_input_file',
                    help="""File with list of attendee addresses.
                            must have first line header of:
                            'email_address'""")
  parser.add_option('-t', dest='threads', default=1, type='int',
                    help="""OPTIONAL: Number of threads to spawn,
                            max of 200.""")
  parser.add_option('-r', dest='max_retry', default=1, type='int',
                    help="""OPTIONAL: Number of additional tries a thread will
                          make to perform the ACL before logging the error and
                          moving on.""")
  parser.add_option('-f', dest='max_failures', default=1, type='int',
                    help="""OPTIONAL: The maximum number of failures allowed
                          before the entire process is terminated.  Failure is
                          defined as a distinct user account that was not able
                          to be updated in the allowable retries.  For example,
                          if max_failures is set to 5 and max_retry is set to
                          3, if there are 6 user accounts for which we tried 4
                          times to update their ACL and failed, we will
                          terminate the process.""")
  parser.add_option('--all', action='store_true', dest='all',
                    help="""If present, will pull the full cal feed
                            but limited to 9999 max events.""")
  parser.add_option('--range', action='store_true', dest='range',
                    help="""If present, expects --start and --end.""")
  parser.add_option('--start', dest='start',
                    help="""Start date. (YYYY-MM-DD)""")
  parser.add_option('--end', dest='end',
                    help="""End date. (YYYY-MM-DD)""")

  (options, args) = parser.parse_args()

  # series of if's to check our flags
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))
  if not options:
    parser.print_help()
    sys.exit(1)

  invalid_args = False
  if options.consumer_key is None:
    print '-k (consumer_key) is required'
    invalid_args = True
  if options.consumer_secret is None:
    print '-s (consumer_secret) is required'
    invalid_args = True
  if options.admin_user is None:
    print '-u (admin_user) is required'
    invalid_args = True
  if options.admin_pass is None:
    print '-p (admin_pass) is required'
    invalid_args = True
  if options.attendee_input_file is None:
    print '-i (attendee_input_file) is required'
    invalid_args = True

  if invalid_args:
    sys.exit(4)

  if not options.all and not options.range:
    print '--all or --range must be specified'
    sys.exit(1)

  if options.all and options.range:
    print 'Cannot pass --all and --range together'
    sys.exit(1)

  if options.range and (not options.start or not options.end):
    print 'when using --range, must pass in --start and --end'
    sys.exit(12)

  # A check on the MAX_THREAD_VALUE from above
  if options.threads > MAX_THREAD_VALUE:
    logging.info('Threads cannot exceed %d, using %d threads instead of %d',
                 MAX_THREAD_VALUE, MAX_THREAD_VALUE, options.threads)
    options.threads = MAX_THREAD_VALUE

  return options


class UserManager(object):
  """Class that builds the list of users that should be audited."""

  def __init__(self, domain, admin_user, admin_pass, attendee_list):
    self.domain = domain
    self.admin_user = admin_user
    self.admin_pass = admin_pass
    self.attendee_list = attendee_list

  def LoadWorkQueue(self, queue):
    """Creates the work queue users eligible to be audited."""

    logging.info('Loading our work queue...')

    for provisioned_user in self._GetAllUsers():
      logging.info('Adding %s to work queue', provisioned_user)
      queue.put(Instruction(self.attendee_list, provisioned_user))

  def _GetServiceConnection(self):
    """Method to establish our Provisioning API Service Connection."""

    logging.info('Logging into the domain...')
    conn = gdata.apps.service.AppsService(email=self.admin_user,
                                          domain=self.domain,
                                          password=self.admin_pass)
    conn.ProgrammaticLogin()
    return conn

  def _GetAllUsers(self):
    """Method to get all non-suspended users from the domain."""

    conn = self._GetServiceConnection()
    logging.info('Getting all the domain users...')
    users = []
    user_feed = conn.RetrieveAllUsers()
    for user_entry in user_feed.entry:
      # Make sure they are not suspended
      if user_entry.login.suspended != 'true':
        email = '%s@%s' % (user_entry.login.user_name, self.domain)
        users.append(email.lower())
    return users


def ValidateInputFile(input_file):

  f = open(input_file, 'r')
  reader = csv.reader(f)
  headers = reader.next()
  reader = csv.DictReader(f, headers)

  # Validate the headers
  if headers[0] == 'email_address':
    pass
  else:
    logging.critical(
        'Invalid header on input file. Please make it: email_address')
    sys.exit(1)


def ReadInputFile(input_filename):
  """Method to read our CSV and create a list."""

  attendees = []
  reader = CSVReader(input_filename)
  for line in reader:
    attendees.append((line['email_address']))
  return attendees


def CSVReader(input_file):
  """Creates a CSV DictReader Object.

  The function opens a csv file and sets the first line of the file as
  headers.  A Dictreader object is then created with these headers.

  Args:
    input_file: [string] filename of CSV file to open.

  Returns:
    DictReader object
  """
  f = open(input_file, 'r')
  reader = csv.reader(f)
  headers = reader.next()
  reader = csv.DictReader(f, headers)
  return reader


def main():

  options = ParseInputs()

  ValidateInputFile(options.attendee_input_file)

  start = time.time()

  # Set up logging
  log_filename = ('print_events_with_attendee_%s.log' %
                  (datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  work_queue = Queue.Queue()
  output_queue = Queue.Queue()
  failure_queue = Queue.Queue()

  # Read in list of attendees to check
  attendee_list = ReadInputFile(options.attendee_input_file)

  # Get All Users Provisioned
  user_mgr = UserManager(options.consumer_key,
                         options.admin_user,
                         options.admin_pass,
                         attendee_list)

  # Load the users eligible for audit into a Queue
  user_mgr.LoadWorkQueue(work_queue)

  # Spawn a pool of threads
  for i in range(options.threads):
    logging.info('Starting thread: %d', (i + 1))
    t = CalendarWorker(options.consumer_key,
                       options.consumer_secret,
                       work_queue,
                       failure_queue,
                       output_queue,
                       options.max_retry,
                       options.max_failures,
                       options)
    t.setDaemon(True)
    t.start()

  # wait on the queue until everything has been processed
  work_queue.join()

  # Print results to output file
  output_filename = ('matching_events_%s.csv' %
                     (datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
  output_file = csv.writer(open(output_filename, 'wb'),
                           delimiter=',',
                           quotechar='"')
  output_file.writerow(['CalendarOwner', 'Organizer', 'Title', 'UID',
                        'StartTime', 'EndTime', 'PublishedTime', 'SyncEvent',
                        'IsRecurrence', 'Participants'])

  while not output_queue.empty():
    next_item = output_queue.get()
    output_file.writerow([next_item.GetCalendarOwner(),
                          next_item.GetOrganizer(),
                          next_item.GetTitle(),
                          next_item.GetUid(),
                          next_item.GetStartTime(),
                          next_item.GetEndTime(),
                          next_item.GetPublishedTime(),
                          next_item.GetSyncEvent(),
                          next_item.GetRecurrence()] +
                         next_item.GetParticipants())

  # print our stats
  logging.info('Summary Statistics:')
  logging.info('Elapsed Time: %s minutes', (time.time() - start) / 60)
  print 'Log file: %s' % (log_filename)
  print 'Output file with found events: %s' % (output_filename)

if __name__ == '__main__':
  main()
