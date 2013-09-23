#!/usr/bin/python
#
# Copyright 2010 Google Inc. All Rights Reserved

"""Copyright (C) 2010 Google Inc. All rights reserved.

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
This script is intended to modify the timezones for a list of users on the
user's primary Google Apps calendar.

Usage:
update_timezones.py -u <admin user> -p <admin password> -k <consumer key>
                       -s <consumer secret> -i <user timezone file>
                       [-t <# threads> -r <# retries> -f <# max failures> -a -c]

The input file should be a two column CSV file with the headers: user,timezone.
The user values need to be the full SMTP address including the domain.
The timezones are required to be in the long web-form (i.e. America/Chicago).

Options:
  -p                    Admin password.
  -u                    Admin user.
  -h, --help            show this help message and exit
  -k CONSUMER_KEY       The consumer key.
  -s CONSUMER_SECRET    The consumer secret.
  -t THREADS            Number of threads to spawn, max of 100.
  -i USER_TIMEZONE_FILE
                        The input file containing users to apply timezone
                        changes for.  File must be a two column CSV
                        with a header of "user" and "timezone".  User must be
                        full SMTP address (e.g. user@domain.com).
  -r MAX_RETRY          Number of additional tries a thread will make to
                        perform the ACL before logging the error and
                        moving on.
  -f MAX_FAILURES       The maximum number of failures allowed before the
                        entire process is terminated.  Failure is defined as
                        a distinct user account that was not able to be
                        updated in the allowable retries.  For example, if
                        max_failures is set to 5 and max_retry is set to
                        3, if there are 6 user accounts for which we tried 4
                        times to update their ACL and failed, we will
                        terminate the process.
  -c                    Create test events (1970-01-01) to assist with
                        the migration.
  -a                    Apply the timezones.

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
from types import TupleType
import atom
import atom.service

import gdata.apps.service
import gdata.calendar
import gdata.calendar.service
import gdata.gauth

MAX_THREAD_VALUE = 100

# Array of failed users
FAILED_USERS = []
# Successful updates
SUCCESSFUL_UPDATES = []
SUCCESSFUL_TIMEZONE_UPDATES = []
SUCCESSFUL_EVENT_CREATIONS = []
SUCCESSFUL_EVENT_DELETIONS = []
# Valid timezones
VALID_TIMEZONES = ['Pacific/Midway', 'Pacific/Honolulu',
                   'Pacific/Tahiti', 'Pacific/Marquesas',
                   'America/Anchorage', 'Pacific/Gambier',
                   'America/Los_Angeles', 'America/Tijuana',
                   'America/Vancouver', 'America/Whitehorse',
                   'Pacific/Pitcairn', 'America/Dawson_Creek',
                   'America/Denver', 'America/Edmonton',
                   'America/Hermosillo', 'America/Mazatlan',
                   'America/Phoenix', 'America/Yellowknife',
                   'America/Belize', 'America/Chicago',
                   'America/Costa_Rica', 'America/El_Salvador',
                   'America/Guatemala', 'America/Managua',
                   'America/Mexico_City', 'America/Regina',
                   'America/Tegucigalpa', 'America/Winnipeg',
                   'Pacific/Easter', 'Pacific/Galapagos',
                   'America/Bogota', 'America/Cayman',
                   'America/Grand_Turk', 'America/Guayaquil',
                   'America/Havana', 'America/Iqaluit',
                   'America/Jamaica', 'America/Lima',
                   'America/Montreal', 'America/Nassau',
                   'America/New_York', 'America/Panama',
                   'America/Port-au-Prince', 'America/Toronto',
                   'America/Caracas', 'America/Anguilla',
                   'America/Antigua', 'America/Aruba',
                   'America/Asuncion', 'America/Barbados',
                   'America/Boa_Vista', 'America/Campo_Grande',
                   'America/Cuiaba', 'America/Curacao',
                   'America/Dominica', 'America/Grenada',
                   'America/Guadeloupe', 'America/Guyana',
                   'America/Halifax', 'America/La_Paz',
                   'America/Manaus', 'America/Martinique',
                   'America/Montserrat', 'America/Port_of_Spain',
                   'America/Porto_Velho', 'America/Puerto_Rico',
                   'America/Rio_Branco', 'America/Santiago',
                   'America/Santo_Domingo', 'America/St_Kitts',
                   'America/St_Lucia', 'America/St_Thomas',
                   'America/St_Vincent', 'America/Thule',
                   'America/Tortola', 'Antarctica/Palmer',
                   'Atlantic/Bermuda', 'Atlantic/Stanley',
                   'America/St_Johns', 'America/Araguaina',
                   'America/Argentina/Buenos_Aires',
                   'America/Bahia', 'America/Belem',
                   'America/Cayenne', 'America/Fortaleza',
                   'America/Godthab', 'America/Maceio',
                   'America/Miquelon', 'America/Montevideo',
                   'America/Paramaribo', 'America/Recife',
                   'America/Sao_Paulo', 'Antarctica/Rothera',
                   'America/Noronha', 'Atlantic/South_Georgia',
                   'America/Scoresbysund', 'Atlantic/Azores',
                   'Atlantic/Cape_Verde', 'Africa/Abidjan',
                   'Africa/Accra', 'Africa/Bamako',
                   'Africa/Banjul', 'Africa/Bissau',
                   'Africa/Casablanca', 'Africa/Conakry',
                   'Africa/Dakar', 'Africa/El_Aaiun',
                   'Africa/Freetown', 'Africa/Lome',
                   'Africa/Monrovia', 'Africa/Nouakchott',
                   'Africa/Ouagadougou', 'Africa/Sao_Tome',
                   'America/Danmarkshavn', 'Atlantic/Canary',
                   'Atlantic/Faroe', 'Atlantic/Reykjavik',
                   'Atlantic/St_Helena', 'Etc/GMT',
                   'Europe/Dublin', 'Europe/Lisbon',
                   'Europe/London', 'Africa/Algiers',
                   'Africa/Bangui', 'Africa/Brazzaville',
                   'Africa/Ceuta', 'Africa/Douala',
                   'Africa/Kinshasa', 'Africa/Lagos',
                   'Africa/Libreville', 'Africa/Luanda',
                   'Africa/Malabo', 'Africa/Ndjamena',
                   'Africa/Niamey', 'Africa/Porto-Novo',
                   'Africa/Tunis', 'Africa/Windhoek',
                   'Europe/Amsterdam', 'Europe/Andorra',
                   'Europe/Belgrade', 'Europe/Berlin',
                   'Europe/Brussels', 'Europe/Budapest',
                   'Europe/Copenhagen', 'Europe/Gibraltar',
                   'Europe/Luxembourg', 'Europe/Madrid',
                   'Europe/Malta', 'Europe/Monaco',
                   'Europe/Oslo', 'Europe/Paris',
                   'Europe/Prague', 'Europe/Rome',
                   'Europe/Stockholm', 'Europe/Tirane',
                   'Europe/Vaduz', 'Europe/Vienna',
                   'Europe/Warsaw', 'Europe/Zurich',
                   'Africa/Blantyre', 'Africa/Bujumbura',
                   'Africa/Cairo', 'Africa/Gaborone',
                   'Africa/Harare', 'Africa/Johannesburg',
                   'Africa/Kigali', 'Africa/Lubumbashi',
                   'Africa/Lusaka', 'Africa/Maputo',
                   'Africa/Maseru', 'Africa/Mbabane',
                   'Africa/Tripoli', 'Asia/Amman',
                   'Asia/Beirut', 'Asia/Damascus',
                   'Asia/Gaza', 'Asia/Jerusalem',
                   'Asia/Nicosia', 'Europe/Athens',
                   'Europe/Bucharest', 'Europe/Chisinau',
                   'Europe/Helsinki', 'Europe/Istanbul',
                   'Europe/Kaliningrad', 'Europe/Kiev',
                   'Europe/Minsk', 'Europe/Riga',
                   'Europe/Sofia', 'Europe/Tallinn',
                   'Europe/Vilnius', 'Africa/Addis_Ababa',
                   'Africa/Asmara', 'Africa/Dar_es_Salaam',
                   'Africa/Djibouti', 'Africa/Kampala',
                   'Africa/Khartoum', 'Africa/Mogadishu',
                   'Africa/Nairobi', 'Antarctica/Syowa',
                   'Asia/Aden', 'Asia/Baghdad',
                   'Asia/Bahrain', 'Asia/Kuwait',
                   'Asia/Qatar', 'Asia/Riyadh',
                   'Europe/Moscow', 'Indian/Antananarivo',
                   'Indian/Comoro', 'Indian/Mayotte',
                   'Asia/Tehran', 'Asia/Baku',
                   'Asia/Dubai', 'Asia/Muscat',
                   'Asia/Tbilisi', 'Asia/Yerevan',
                   'Europe/Samara', 'Indian/Mahe',
                   'Indian/Mauritius', 'Indian/Reunion',
                   'Asia/Kabul', 'Asia/Aqtau',
                   'Asia/Aqtobe', 'Asia/Ashgabat',
                   'Asia/Dushanbe', 'Asia/Karachi',
                   'Asia/Tashkent', 'Asia/Yekaterinburg',
                   'Indian/Kerguelen', 'Indian/Maldives',
                   'Asia/Calcutta', 'Asia/Colombo',
                   'Asia/Katmandu', 'Antarctica/Mawson',
                   'Antarctica/Vostok', 'Asia/Almaty',
                   'Asia/Bishkek', 'Asia/Dhaka',
                   'Asia/Omsk', 'Asia/Thimphu',
                   'Indian/Chagos', 'Asia/Rangoon',
                   'Indian/Cocos', 'Antarctica/Davis',
                   'Asia/Bangkok', 'Asia/Hovd',
                   'Asia/Jakarta', 'Asia/Krasnoyarsk',
                   'Asia/Phnom_Penh', 'Asia/Saigon',
                   'Asia/Vientiane', 'Indian/Christmas',
                   'Antarctica/Casey', 'Asia/Brunei',
                   'Asia/Choibalsan', 'Asia/Hong_Kong',
                   'Asia/Irkutsk', 'Asia/Kuala_Lumpur',
                   'Asia/Macau', 'Asia/Makassar',
                   'Asia/Manila', 'Asia/Shanghai',
                   'Asia/Singapore', 'Asia/Taipei',
                   'Asia/Ulaanbaatar', 'Australia/Perth',
                   'Asia/Dili', 'Asia/Jayapura',
                   'Asia/Pyongyang', 'Asia/Seoul',
                   'Asia/Tokyo', 'Asia/Yakutsk',
                   'Pacific/Palau', 'Australia/Adelaide',
                   'Australia/Darwin', 'Antarctica/DumontDUrville',
                   'Asia/Vladivostok', 'Australia/Brisbane',
                   'Australia/Hobart', 'Australia/Sydney',
                   'Pacific/Guam', 'Pacific/Port_Moresby',
                   'Pacific/Saipan', 'Pacific/Truk',
                   'Asia/Magadan', 'Pacific/Efate',
                   'Pacific/Guadalcanal', 'Pacific/Kosrae',
                   'Pacific/Noumea', 'Pacific/Ponape',
                   'Pacific/Norfolk', 'Asia/Kamchatka',
                   'Pacific/Auckland', 'Pacific/Fiji',
                   'Pacific/Funafuti', 'Pacific/Kwajalein',
                   'Pacific/Majuro', 'Pacific/Nauru',
                   'Pacific/Tarawa', 'Pacific/Wake',
                   'Pacific/Wallis', 'Pacific/Enderbury',
                   'Pacific/Tongatapu', 'Pacific/Kiritimati']


class AclInstruction(object):
  """Class to hold instructions for updating timezones."""

  def __init__(self, username, timezone):
    self.username = username
    self.timezone = timezone

  def __str__(self):
    return ('AclInstruction{UserName:[%s],Timezone:[%s]}' %
            (self.username, self.timezone))

  def GetUserName(self):
    return self.username

  def GetTimezone(self):
    return self.timezone


class CalendarWorker(threading.Thread):
  """Threaded calendar worker."""

  def __init__(self, consumer_key, consumer_secret, work_queue, failure_queue,
               timezone_decision_queue, max_retry, max_failures,
               create_test_events, apply_timezones):
    """Creates a CalendarService and provides Oauth auth details to it."""

    threading.Thread.__init__(self)
    self.consumer_key = consumer_key
    self.consumer_secret = consumer_secret
    self.sig_method = gdata.auth.OAuthSignatureMethod.HMAC_SHA1
    self.work_queue = work_queue
    self.failure_queue = failure_queue
    self.timezone_decision_queue = timezone_decision_queue
    self.max_retry = max_retry
    self.max_failures = max_failures
    self.create_test_events = create_test_events
    self.apply_timezones = apply_timezones
    self.event_title = 'Calendar Initialization Event - Ignore (Migration)'
    self.event_date = datetime.date(1970, 01, 01)

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
            logging.warning('\tException when processing [%s]: %s',
                            task.GetUserName(), str(err))
            retry_count += 1
            logging.info('\tRetrying user: [%s] (%s/%s)',
                         task.GetUserName(), retry_count, self.max_retry)
        else:
          logging.error('\tMax retries hit for [%s], skipping',
                        task.GetUserName())
          self.failure_queue.put(task)
          FAILED_USERS.append(task.GetUserName())
      else:
        logging.error("""Max failures reached for this run.
                      Skipping all subsequent entries.""")
        FAILED_USERS.append(task.GetUserName())

      # signals to queue job is done
      self.work_queue.task_done()

  def _ProcessInstruction(self, task):
    # TODO(mirons): track unchanged users.

    connection = self._GetCalendarServiceConnection(task.GetUserName())

    if self.apply_timezones:

      if (task.GetTimezone() != self._ExistingTimezone(connection,
                                                       task.GetUserName())):
        # update the timezone
        try:
          logging.info('\t[%s] Updating timezone for [%s] to [%s]',
                       self.name, task.GetUserName(), task.GetTimezone())
          self._UpdateTimezone(connection, task)
          self.timezone_decision_queue.put((task, 'updated'))
          SUCCESSFUL_TIMEZONE_UPDATES.append(task.GetUserName())
        except gdata.calendar.service.RequestError, req_err:
          logging.error('\tRequestError received during timezone update: %s',
                        str(req_err))
          raise
        except Exception, err:
          logging.error('\t[%s] Error updating the timezone for [%s]: %s',
                        self.name, task.GetUserName(), str(err))
          raise

      else:
        logging.info('\t[%s] No timezone to set for [%s], timezone is [%s]',
                     self.name, task.GetUserName(), task.GetTimezone())
        self.timezone_decision_queue.put((task, 'no-op'))
    else:
      logging.info('\t[%s] Told to not set a timezone for [%s]',
                   self.name, task.GetUserName())

    if self.create_test_events:
      if not self._CalendarIsInitialized(connection):
        # create the single event
        try:
          logging.info('\t[%s] Creating a single event for [%s]',
                       self.name, task.GetUserName())
          new_event = self._InsertSingleEvent(connection, task)
          SUCCESSFUL_EVENT_CREATIONS.append(task.GetUserName())
        except gdata.calendar.service.RequestError, req_err:
          logging.error('RequestError received during event insert: %s',
                        str(req_err))
          raise
        except Exception, err:
          logging.error('[%s] Error creating a single event for [%s]: %s',
                        self.name, task.GetUserName(), str(err))
          raise
      else:
        logging.info("""\t[%s] Calendar is already initialized, skipping event creation for [%s]""",
                     self.name, task.GetUserName())
    else:
      logging.info('\t[%s] Told not not create an event for [%s]',
                   self.name, task.GetUserName())

  def _GetCalendarServiceConnection(self, username):
    """Method to create our Connection."""

    conn = gdata.calendar.service.CalendarService(source='timezone_update')
    conn.SetOAuthInputParameters(signature_method=self.sig_method,
                                 consumer_key=self.consumer_key,
                                 consumer_secret=self.consumer_secret,
                                 two_legged_oauth=True,
                                 requestor_id=username)
    return conn

  def _ExistingTimezone(self, connection, username):
    """Method to check to see if the Calendar timezone is correct."""

    feed = connection.GetOwnCalendarsFeed()

    for cal in feed.entry:
      # TODO(mdauphinee): Confirm that this is the best way to grab the primary
      #                   cal
      if cal.title.text == username:
        return cal.timezone.value

    return None

  def _UpdateTimezone(self, conn, task):
    """Method to add our sharing."""

    feed = conn.GetOwnCalendarsFeed()
    for cal in feed.entry:
      if cal.title.text == task.GetUserName():
        cal.timezone = gdata.calendar.Timezone(value=task.GetTimezone())
        updated_calendar = conn.UpdateCalendar(calendar=cal)
        logging.info('\t[%s] Reading the timezone for user [%s]: [%s]',
                     self.name, task.GetUserName(),
                     updated_calendar.timezone.value)
      else:
        pass

  # method to create a single test event to initiate the calendar so calendars
  # can be migrated properly 
  def _InsertSingleEvent(self, calendar_service, task):

    # setup the event details
    title = self.event_title
    content = 'Ignore'
    where = 'Not Applicable'
    start_time = '%sT01:00:00.000Z' % (self.event_date.strftime("%Y-%m-%d"))
    end_time = '%sT02:00:00.000Z' % (self.event_date.strftime("%Y-%m-%d"))

    event = gdata.calendar.CalendarEventEntry()
    event.title = atom.Title(text=title)
    event.content = atom.Content(text=content)
    event.where.append(gdata.calendar.Where(value_string=where))

    event.when.append(gdata.calendar.When(start_time=start_time,
                                          end_time=end_time))

    url = '/calendar/feeds/default/private/full'
    new_event = calendar_service.InsertEvent(event, url)

    logging.info('\t[%s] New single event inserted for [%s][%s]',
                 self.name, task.GetUserName(), new_event.id.text)

    return new_event

  def _DeleteSingleEvent(self, calendar_service, event):
    calendar_service.DeleteEvent(event.GetEditLink().href)

  def _CalendarIsInitialized(self, calendar_service):

    query = gdata.calendar.service.CalendarEventQuery('default',
                                                      'private',
                                                      'full')
    query.start_min = self.event_date.strftime("%Y-%m-%d")
    delta = datetime.timedelta(days=1)
    query.start_max = (self.event_date + delta).strftime("%Y-%m-%d")

    feed = calendar_service.CalendarQuery(query)
    for event in feed.entry:
      if event.title.text == self.event_title:
        return True
      else:
        pass

    return False


class UserManager(object):
  """Class that perfoms all user actions and sets up the work queue."""

  def __init__(self, admin_user, admin_pass, domain):

    self.admin_user = admin_user
    self.admin_pass = admin_pass
    self.domain = domain

  def LoadWorkQueue(self, queue, users):
    """Creates the work queue with an action for each user in the given file."""

    logging.info('\tLoading our work queue...')

    for u, tz in users.items():
      queue.put(AclInstruction(u, tz))
      logging.info('Added %s:%s to work queue', u, tz)

  def _GetServiceConnection(self):
    """Method to establish our Service Connection."""

    logging.info('\tLogging into the domain...')

    # TODO(mirons): Convert to OAuth
    conn = gdata.apps.service.AppsService(email=self.admin_user,
                                          domain=self.domain,
                                          password=self.admin_pass)
    conn.ProgrammaticLogin()

    return conn

  def _ReadUsersFile(self, user_filename):
    """Method to read our CSV and create an array of users."""

    logging.info('\tGathering our users...')
    users = []
    reader = CSVReader(user_filename)
    for line in reader:
      users.append((line['user'].lower(), line['timezone']))
    return users

  def _GetAllUsers(self):
    """Retrieves all users and their suspended state from domain."""

    conn = self._GetServiceConnection()
    logging.info('\tGetting all the domain users...')
    users = {}
    user_feed = conn.RetrieveAllUsers()
    for user_entry in user_feed.entry:
      address = '%s@%s' % (user_entry.login.user_name,
                           self.domain)
      users[address.lower()] = user_entry.login.suspended
    return users

  def PartitionFileEntries(self, user_filename):
    """Validates and separates entries from the input file."""

    unique_records = []
    dup_records = []
    users_not_in_domain = []
    users_not_in_input_file = []
    users_suspended = []
    valid_users = {}
    dup_users = []
    deduped_users = {}

    domain_users = self._GetAllUsers()
    input_file_users = self._ReadUsersFile(user_filename)

    # Capture identical records
    for (u, tz) in input_file_users:
      if (u, tz) in unique_records:
        dup_records.append((u, tz))
      else:
        unique_records.append((u, tz))

    # Capture records where the username is listed twice with different
    # timezones. Both records will be written to file and skipped.
    user_counts = {}
    for (u, tz) in unique_records:
      if u in user_counts:
        user_counts[u] += 1
      else:
        user_counts[u] = 1

    for (u, tz) in unique_records:
      if user_counts[u] > 1:
        dup_users.append((u, tz))
      elif user_counts[u] == 1:
        deduped_users[u] = tz

    for u in domain_users:
      if u not in deduped_users.keys():
        logging.warning('Found a domain user not in the input file: %s',
                        u)
        users_not_in_input_file.append(u)
    for u, tz in deduped_users.items():
      if u not in domain_users.keys():
        logging.warning('Found user in input file but not in the domain: %s',
                        u)
        users_not_in_domain.append(u)
      elif domain_users[u].lower() == 'true':
        logging.warning('Found a user in the input file who is suspended: %s',
                        u)
        users_suspended.append(u)
      else:
        valid_users[u] = tz

    return (input_file_users, dup_records, dup_users, users_not_in_domain,
            users_not_in_input_file, users_suspended, valid_users)


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""
  usage = """%prog -u <admin user> -p <admin password> -k <consumer key>
          -s <consumer secret> -i <user timezone file> [-a -c -t <# threads>
          -r <# retries> -f <# max failures>]\n"""
  parser = OptionParser(usage=usage)
  parser.add_option('-p', dest='admin_pass',
                    help="""Admin password.""")
  parser.add_option('-u', dest='admin_user',
                    help="""Admin user.""")
  parser.add_option('-k', dest='consumer_key',
                    help="""The consumer key.""")
  parser.add_option('-s', dest='consumer_secret',
                    help="""The consumer secret.""")
  parser.add_option('-t', dest='threads', default=1, type='int',
                    help="""Number of threads to spawn, max of 100.""")
  parser.add_option('-i', dest='user_timezone_file',
                    help="""The input file containing user timezones.""")
  parser.add_option('-r', dest='max_retry', default=1, type='int',
                    help="""Number of additional tries a thread will make to
                          perform the ACL before logging the error and
                          moving on.""")
  parser.add_option('-f', dest='max_failures', default=1, type='int',
                    help="""The maximum number of failures allowed before the
                          entire process is terminated.  Failure is defined as
                          a distinct user account that was not able to be
                          updated in the allowable retries.  For example, if
                          max_failures is set to 5 and max_retry is set to
                          3, if there are 6 user accounts for which we tried 4
                          times to update their ACL and failed, we will
                          terminate the process.""")
  parser.add_option('-c', dest='create_test_events', action='store_true',
                    default=False,
                    help="""Create test events (1970-01-01) to assist with
                            the migration.""")
  parser.add_option('-a', dest='apply_timezones', action='store_true',
                    default=False,
                    help="""Apply the timezones.""")

  (options, args) = parser.parse_args()

  # series of if's to check our flags
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))
  if not options:
    parser.print_help()
    sys.exit(1)
  if options.consumer_key is None:
    print '-k (consumer_key) is required'
    sys.exit(1)
  if options.consumer_secret is None:
    print '-s (consumer_secret) is required'
    sys.exit(1)
  if options.user_timezone_file is None:
    print '-i (user timezone file) is required.'
    sys.exit(1)
  if options.admin_user is None:
    print '-u (admin user) is required.'
    sys.exit(1)
  if options.admin_pass is None:
    print '-p (admin password) is required.'
    sys.exit(1)
  if not options.create_test_events and not options.apply_timezones:
    print 'You told us to do nothing (-a and -c).'
    sys.exit(1)

  # A check on the MAX_THREAD_VALUE from above
  if options.threads > MAX_THREAD_VALUE:
    logging.info('Threads cannot exceed %d, using %d threads instead of %d',
                 MAX_THREAD_VALUE, MAX_THREAD_VALUE, options.threads)
    options.threads = MAX_THREAD_VALUE

  # Let the user know of the actions were going to take
  if options.create_test_events and not options.apply_timezones:
    logging.info('\n!!!We are only going to create events!!!\n')
  elif options.create_test_events and options.apply_timezones:
    logging.info('\n!!!We are going to set timezones and create events!!!\n')
  else:
    logging.info('\n!!!We are only going to set timezones!!!\n')

  return options


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


def ValidateInputFile(input_file):
  """Validates the input file against VALID_TIMEZONES.

  The function opens the input file, reads the first line as a header.
  Then loops through the dictreader looking for an invalid timezone.

  Args:
    input_file: [string] filename of CSV file to open.

  Returns:
    nothing
  """

  f = open(input_file, 'r')
  reader = csv.reader(f)
  headers = reader.next()
  reader = csv.DictReader(f, headers)

  # Validate the headers
  if headers[0] == 'user' and headers[1] == 'timezone':
    pass
  else:
    logging.critical('Invalid header. Please make it: user,timezone')
    sys.exit(1)

  # Validate the file for timezones
  for line in reader:
    if line['timezone'] not in VALID_TIMEZONES:
      logging.critical('Invalid timezone in the input file: %s [Line: %s]',
                       line['timezone'], (reader.line_num + 1))
      sys.exit(1)


def WriteFile(filename, data):
  if data:
    f = csv.writer(open(filename, 'wb'), delimiter=',')
    for e in data:
      if type(e) is TupleType:
        f.writerow([e[0], e[1]])
      else:
        f.writerow([e])
    logging.info('File %s created', filename)


def main():
  start = time.time()

  run_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

  # Set up logging
  log_filename = ('update_timezones_%s.log' % run_timestamp)
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  options = ParseInputs()

  logging.info('Preparing our environment')

  # Validate the input file
  logging.info('\tChecking the input file for valid timezones...')
  ValidateInputFile(options.user_timezone_file)

  work_queue = Queue.Queue()
  failure_queue = Queue.Queue()
  timezone_decision_queue = Queue.Queue()

  user_mgr = UserManager(options.admin_user, options.admin_pass,
                         options.consumer_key)

  # Separate the input file entries
  (input_file_users, dup_records, dup_users, unknown_users,
   overlooked_users, suspended_users,
   valid_users) = user_mgr.PartitionFileEntries(options.user_timezone_file)

  # Write out bad records
  # duplicate records (user given more than once with same timezone)
  duplicate_records_filename = ('duplicate_records_%s.csv' % run_timestamp)
  logging.info('Writing %s...', duplicate_records_filename)
  WriteFile(duplicate_records_filename, dup_records)

  # duplicate users (user given more than once with more than one timezone)
  duplicate_users_filename = ('duplicate_users_%s.csv' % run_timestamp)
  logging.info('Writing %s...', duplicate_users_filename)
  WriteFile(duplicate_users_filename, dup_users)

  # unknown users
  unknown_users_filename = ('unknown_users_%s.csv' % run_timestamp)
  logging.info('Writing %s...', unknown_users_filename)
  WriteFile(unknown_users_filename, unknown_users)

  # overlooked users
  overlooked_users_filename = ('overlooked_users_%s.csv' % run_timestamp)
  logging.info('Writing %s...', overlooked_users_filename)
  WriteFile(overlooked_users_filename, overlooked_users)

  # suspended users
  suspended_users_filename = ('suspended_users_%s.csv' % run_timestamp)
  logging.info('Writing %s...', suspended_users_filename)
  WriteFile(suspended_users_filename, suspended_users)

  # Load the instructions for each user into a Queue
  user_mgr.LoadWorkQueue(work_queue, valid_users)

  # Spawn a pool of threads
  for i in range(options.threads):
    logging.info('Starting thread: %d...', (i + 1))
    t = CalendarWorker(options.consumer_key,
                       options.consumer_secret,
                       work_queue,
                       failure_queue,
                       timezone_decision_queue,
                       options.max_retry,
                       options.max_failures,
                       options.create_test_events,
                       options.apply_timezones)
    t.setDaemon(True)
    t.start()

  # wait on the queue until everything has been processed
  work_queue.join()

  # print our stats
  logging.info('============ All Work Queues are Done ============')
  logging.info('Summary Statistics:')
  logging.info('\tElapsed Time: %s minutes',
               round(((time.time() - start) / 60), 2))
  logging.info('User Statistics:')

  if overlooked_users:
    logging.info('\tNumber of users in the domain, but missing from file: %s',
                 len(overlooked_users))

  logging.info('\tNumber of entries in file: %d', len(input_file_users))
  if dup_records or dup_users or unknown_users or suspended_users:
    logging.info('\t\tFile Reductions:')
  if dup_records:
    logging.info('\t\tNumber of duplicate records '
                 '(same user and timezone) in file: %d', len(dup_records))
  if dup_users:
    logging.info('\t\tNumber of duplicate user timezones '
                 '(same user and diff timezone) in file: %d', len(dup_users))
  if unknown_users:
    logging.info('\t\tNumber of unknown users: %s',
                 len(unknown_users))
  if suspended_users:
    logging.info('\t\tNumber of suspended users: %s',
                 len(suspended_users))
  logging.info('\tNumber of valid users we worked on: %s',
               len(valid_users))

  # Parse queue to determine users updated
  completed_users = {}
  while not timezone_decision_queue.empty():
    (task, operation) = timezone_decision_queue.get()
    if task.GetUserName() in completed_users:
      if (completed_users[task.GetUserName()] == 'updated'
          and operation == 'no-op'):
        pass
      elif (completed_users[task.GetUserName()] == 'no-op'
            and operation == 'updated'):
        completed_users[task.GetUserName()] = 'updated'
      elif completed_users[task.GetUserName()] == operation:
        pass
      else:
        logging.error('Problem reading timezone_decision_queue, '
                      'entries are corrupt')
    else:
      completed_users[task.GetUserName()] = operation
    timezone_decision_queue.task_done()

  logging.info('\tNumber of successful timezone updates: %s',
               len(SUCCESSFUL_TIMEZONE_UPDATES))

  logging.info('\tNumber of successful timezone updates (synchronized): %s',
               sum([1 for i in completed_users.values() if i == 'updated']))
  logging.info('\tNumber of unchanged timezones (synchronized): %s',
               sum([1 for i in completed_users.values() if i == 'no-op']))

  if options.create_test_events:
    logging.info('\tNumber of successful event creations: %s',
                 len(SUCCESSFUL_EVENT_CREATIONS))
    logging.info('\tNumber of successful event deletions: %s',
                 len(SUCCESSFUL_EVENT_DELETIONS))

  logging.info('\tNumber of failed users '
               '(unable to complete both tz update and event creation): %s',
               len(FAILED_USERS))

  # log failed users if we had them
  if FAILED_USERS:
    logging.info('\tFailed users: %s', ','.join(FAILED_USERS))
  print '\tLog file: %s' % (log_filename)

if __name__ == '__main__':
  main()
