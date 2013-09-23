#!/usr/bin/python2.6
#
# Copyright 2010 Google Inc. All Rights Reserved.

"""Copyright (C) 2010 Google Inc.
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
This is typically needed in Google Apps deployment co-existence where a
free/busy tool has been installed (GCC/GCCLN) and we do not want the accounts
provisioned to Google Apps to respond to requests yet.

Removes calendar sharing for users not in given file. If the -R flag is given it
will reapply the default sharing for all users in the domain. The excluded users
file requires a header of 'users'.  The users file must also have users listed
with their domain, e.g. user@domain.com

Caveats:

This has not been written with Multi-Domain in mind.  It is almost gauranteed to
not work with users outside of your primary domain.

Usage:

Normal Usage: update_calendar_acl.py -k <consumer key> -s <consumer secret>
  -u <admin user> -p <admin password> -e <excluded users file>
  [-t <# threads> -r <# retries> -f <# max failures>

Reset the domain: update_calendar_acl.py -k <consumer key> -s <consumer secret>
  -u <admin user> -p <admin password> -R [-t <# threads> -r <#retries>
  -f <# max failures]

Options:
  -h, --help            show this help message and exit
  -R                    Enable sharing for everyone in the domain.
                        In this situation the excluded users input file
                        is not needed.
  -k CONSUMER_KEY       The consumer key.
  -s CONSUMER_SECRET    The consumer secret.
  -u ADMIN_USER         Admin user for the Provisioning API,
                        e.g. user@domain.com.
  -p ADMIN_PASS         Admin password for the Provisioning API.
  -t THREADS            Number of threads to spawn, max of 100.
  -e EXCLUDED_USERS_FILE
                        The input file containing users that
                        will keep cal sharing. File must be a single column
                        with a header of "users", e.g. user@domain.com.
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

MAX_THREAD_VALUE = 100

# Array of failed users
FAILED_USERS = []
# Succesful Shared Users
SUCCESSFUL_SHARED_USERS = []
# Sucessful Un-shared Users
SUCCESSFUL_UN_SHARED_USERS = []
# Users we did not act on
UNCHANGED_USERS = []


class AclInstruction(object):
  """Class to hold instructions for updating ACLs."""

  def __init__(self, username, is_cal_domain_shared):
    self.username = username
    self.is_cal_domain_shared = is_cal_domain_shared

  def __str__(self):
    return ('AclInstruction{UserName:[%s],Shared:[%s]}' %
            (self.username, self.is_cal_domain_shared))

  def GetUserName(self):
    return self.username

  def GetIsCalDomainShared(self):
    return self.is_cal_domain_shared


class CalendarWorker(threading.Thread):
  """Threaded calendar worker."""

  def __init__(self, consumer_key, consumer_secret, work_queue, failure_queue,
               max_retry, max_failures):
    """Creates a CalendarService and provides Oauth auth details to it."""

    threading.Thread.__init__(self)
    self.consumer_key = consumer_key
    self.consumer_secret = consumer_secret
    self.sig_method = gdata.auth.OAuthSignatureMethod.HMAC_SHA1
    self.work_queue = work_queue
    self.failure_queue = failure_queue
    self.max_retry = max_retry
    self.max_failures = max_failures

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
            logging.warning("Exception when processing [%s]: %s\n",
                            task.GetUserName(), str(err))
            retry_count += 1
            logging.info("Retrying user: [%s] (%s/%s)",
                         task.GetUserName(), retry_count, self.max_retry)
        else:
          logging.error("Max retries hit for [%s], skipping\n",
                        task.GetUserName())
          self.failure_queue.put(task)
          FAILED_USERS.append(task.GetUserName())
      else:
        logging.error("""Max failures reached for user: [%s] (skipping all
                      subsequent entries).""", task.GetUserName())
        FAILED_USERS.append(task.GetUserName())

      # signals to queue job is done
      self.work_queue.task_done()

  def _ProcessInstruction(self, task):
    connection = self._GetCalendarServiceConnection(task.GetUserName())

    # actually perform the work
    if (task.GetIsCalDomainShared() and
        not self._ExistingCalDomainShared(connection)):
      logging.info("[%s] Adding sharing for [%s]",
                   self.name, task.GetUserName())
      self._AddDomainSharing(connection)
      SUCCESSFUL_SHARED_USERS.append(task.GetUserName())
    elif (not task.GetIsCalDomainShared() and
          self._ExistingCalDomainShared(connection)):
      logging.info("[%s] Removing sharing for [%s]",
                   self.name, task.GetUserName())
      self._RemoveDomainSharing(connection)
      SUCCESSFUL_UN_SHARED_USERS.append(task.GetUserName())
    else:
      logging.info("[%s] Nothing to do for user: [%s]",
                   self.name, task.GetUserName())
      UNCHANGED_USERS.append(task.GetUserName())

  def _GetCalendarServiceConnection(self, username):
    """Method to create our Connection."""

    conn = gdata.calendar.service.CalendarService(source="acl_update")
    conn.SetOAuthInputParameters(signature_method=self.sig_method,
                                 consumer_key=self.consumer_key,
                                 consumer_secret=self.consumer_secret,
                                 two_legged_oauth=True,
                                 requestor_id=username)
    return conn

  def _ExistingCalDomainShared(self, connection):
    """Method to check to see if the Calendar is already shared."""

    feed = connection.GetCalendarAclFeed()

    for acl_entry in feed.entry:
      if acl_entry.scope.type == 'domain':
        return True

    return False

  def _AddDomainSharing(self, conn):
    """Method to add our sharing."""

    rule = gdata.calendar.CalendarAclEntry()
    rule.scope = gdata.calendar.Scope(value=self.consumer_key,
                                      scope_type='domain')
    role_value = 'http://schemas.google.com/gCal/2005#%s' % ('read')
    rule.role = gdata.calendar.Role(value=role_value)
    acl_url = '/calendar/feeds/default/acl/full'
    returned_rule = conn.InsertAclEntry(rule, acl_url)
    return returned_rule

  def _RemoveDomainSharing(self, conn):
    """Method to remove the sharing."""

    feed = conn.GetCalendarAclFeed()
    for acl_entry in feed.entry:
      if acl_entry.scope.type == 'domain':
        conn.DeleteAclEntry(acl_entry.GetEditLink().href)


class UserManager(object):
  """Class that perfoms all user actions and sets up the work queue."""

  def __init__(self, domain, admin_user, admin_pass):
    self.domain = domain
    self.admin_user = admin_user
    self.admin_pass = admin_pass

  def LoadWorkQueue(self, queue, revert_domain, excluded_users_file):
    """Creates the work queue with an action for each user in the domain."""

    logging.info("Loading our work queue...")

    if excluded_users_file:
      excluded_users = self._ReadUsersFile(excluded_users_file)
    elif revert_domain:
      logging.info("Reverting the Domain...")

    all_provisioned_users = self._GetAllUsers()

    # Configuring our work queue for each user
    for provisioned_user in all_provisioned_users:
      if revert_domain:
        logging.info("Adding %s to work queue", provisioned_user)
        queue.put(AclInstruction(provisioned_user, True))
      else:
        if provisioned_user not in excluded_users:
          logging.info("Adding %s to work queue", provisioned_user)
          queue.put(AclInstruction(provisioned_user, False))
        else:
          logging.info("Adding %s to work queue", provisioned_user)
          queue.put(AclInstruction(provisioned_user, True))

  def _GetServiceConnection(self):
    """Method to establish our Service Connection."""

    logging.info("Logging into the domain...")
    conn = gdata.apps.service.AppsService(email=self.admin_user,
                                          domain=self.domain,
                                          password=self.admin_pass)
    conn.ProgrammaticLogin()
    return conn

  def _ReadUsersFile(self, user_filename):
    """Method to read our CSV and create an array of users."""

    logging.info("Reading in the users file...")
    users = []
    reader = CSVReader(user_filename)
    for line in reader:
      users.append(line['users'].lower())
    return users

  def _GetAllUsers(self):
    """Method to get all users from the domain."""

    conn = self._GetServiceConnection()
    logging.info("Getting all the domain users...")
    users = []
    user_feed = conn.RetrieveAllUsers()
    for user_entry in user_feed.entry:
      # Make sure they are not suspended
      if user_entry.login.suspended != 'true':
        email = '%s@%s' % (user_entry.login.user_name, self.domain)
        users.append(email.lower())
    return users


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""
  usage = """%prog -k <consumer key> -s <consumer secret> -u <admin user> -p
              <admin password> -e <excluded users file> [-t <# threads> -r <#
              retries> -f <# max failures>\n
              Reset the domain: %prog -k <consumer key> -s <consumer secret> -u
              <admin user> -p <admin password> -R [-t <# threads> -r <#retries>
              -f <# max failures]"""
  parser = OptionParser(usage=usage)
  parser.add_option('-R',
                    dest='revert_domain',
                    action="store_true",
                    default=False,
                    help="""Enable sharing for everyone in the domain.
                            In this situation the excluded users input file
                            is not needed.""")
  parser.add_option('-k', dest='consumer_key',
                    help="""The consumer key.""")
  parser.add_option('-s', dest='consumer_secret',
                    help="""The consumer secret.""")
  parser.add_option('-u', dest='admin_user',
                    help="""Admin user for the Provisioning API,
                            e.g. user@domain.com.""")
  parser.add_option('-p', dest='admin_pass',
                    help="""Admin password for the Provisioning API.""")
  parser.add_option('-t', dest='threads', default=1, type="int",
                    help="""Number of threads to spawn, max of 100.""")
  parser.add_option('-e', dest='excluded_users_file',
                    help="""The input file containing users that
                          will keep cal sharing. File must be a single column
                          with a header of "users", e.g. user@domain.com.""")
  parser.add_option('-r', dest='max_retry', default=1, type="int",
                    help="""Number of additional tries a thread will make to
                          perform the ACL before logging the error and
                          moving on.""")
  parser.add_option('-f', dest='max_failures', default=1, type="int",
                    help="""The maximum number of failures allowed before the
                          entire process is terminated.  Failure is defined as
                          a distinct user account that was not able to be
                          updated in the allowable retries.  For example, if
                          max_failures is set to 5 and max_retry is set to
                          3, if there are 6 user accounts for which we tried 4
                          times to update their ACL and failed, we will
                          terminate the process.""")

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
  if options.admin_user is None:
    print '-u (adminuser@domain.com) is required'
    sys.exit(1)
  if options.admin_pass is None:
    print '-p (admin pass) is required'
    sys.exit(1)
  if options.excluded_users_file is None and not options.revert_domain:
    print 'Either -e (excluded users file)  or -R (revert domain) is required.'
    sys.exit(1)

  # A check on the MAX_THREAD_VALUE from above
  if options.threads > MAX_THREAD_VALUE:
    logging.info("Threads cannot exceed %d, using %d threads instead of %d",
                 MAX_THREAD_VALUE, MAX_THREAD_VALUE, options.threads)
    options.threads = MAX_THREAD_VALUE

  return options


def GetTimeStamp():
  now = datetime.datetime.now()
  return now.strftime('%Y%m%d%H%M%S')


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

  start = time.time()

  # Set up logging
  log_filename = ('update_calendar_acl_%s.log' %
                  (datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  work_queue = Queue.Queue()
  failure_queue = Queue.Queue()

  # Get All Users Provisioned
  user_mgr = UserManager(options.consumer_key,
                         options.admin_user,
                         options.admin_pass)

  # Load the instructions for each user into a Queue
  user_mgr.LoadWorkQueue(work_queue, options.revert_domain,
                         options.excluded_users_file)

  # Spawn a pool of threads
  for i in range(options.threads):
    logging.info("Starting thread: %d", (i + 1))
    t = CalendarWorker(options.consumer_key,
                       options.consumer_secret,
                       work_queue,
                       failure_queue,
                       options.max_retry,
                       options.max_failures)
    t.setDaemon(True)
    t.start()

  # wait on the queue until everything has been processed
  work_queue.join()
  # print our stats
  logging.info("============ All Work Queues are Done ============")
  logging.info("Summary Statistics:")
  logging.info("Elapsed Time: %s minutes", (time.time() - start) / 60)
  logging.info("# of successful users we added sharing for: %s",
               len(SUCCESSFUL_SHARED_USERS))
  logging.info("# of successful users we removed sharing for: %s",
               len(SUCCESSFUL_UN_SHARED_USERS))
  logging.info("# of unchanged users: %s",
               len(UNCHANGED_USERS))
  logging.info("# of failed users: %s",
               len(FAILED_USERS))

  # print failed users if we had them
  if FAILED_USERS:
    logging.info("failed users: \n%s", FAILED_USERS)
  print "Log file: %s" % (log_filename)

if __name__ == '__main__':
  main()
