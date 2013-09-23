#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.

"""Reference implementation of IMAP/POP enforcement script.


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
This program is intended to check the IMAP and POP settings for all users in
the domain.  If the users are not in an approved users Google Group, IMAP and
POP will be disabled.

Usage: enforce_imap_policy.py -k <consumer key> -s <consumer secret>
               -d <domain> -u <admin user> -p <admin password>
              [-g <authorized users group> -t <# threads> -r <max_retries>]

Options:
  -h, --help          show this help message and exit
  -k CONSUMER_KEY     The consumer key.
  -s CONSUMER_SECRET  The consumer secret.
  -d DOMAIN           The Google Apps domain.
  -u ADMIN_USER       Admin user for the Provisioning API,
                      e.g. user@domain.com.
  -p ADMIN_PASS       Admin password for the Provisioning API.
  -g EXCEPTION_GROUP  Google Group containing users authorized to
                      use IMAP
  -t THREADS          Number of threads to spawn, max of 100.
  -r MAX_RETRIES      Maximum number of retries before giving up on user.

"""


__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import datetime
import logging
from optparse import OptionParser
import Queue
import sys
import threading
import time

import gdata.apps.emailsettings.client
import gdata.apps.groups.service as groups_service
import gdata.apps.service
import gdata.calendar
import gdata.calendar.service
import gdata.gauth


# A arbitrary ceiling to the number of threads
# that can be started.
MAX_THREAD_VALUE = 100

# Array of failed users
FAILED_USERS = []
# Succesfully modified users
SUCCESSFUL_IMAP_DISABLED_USERS = []
SUCCESSFUL_POP_DISABLED_USERS = []
# Users we did not act on
UNCHANGED_IMAP_USERS = []
UNCHANGED_POP_USERS = []


class WorkerInstruction(object):
  """Class to hold instructions for updating email settings."""

  def __init__(self, username):
    self.username = username

  def __str__(self):
    return ('WorkerInstruction{UserName:[%s]}' %
            (self.username))

  def GetUserName(self):
    return self.username


class Worker(threading.Thread):
  """Threaded calendar worker."""

  def __init__(self, consumer_key, consumer_secret, domain,
               admin_user, admin_pass, max_retries, work_queue,
               failure_queue):
    threading.Thread.__init__(self)
    self.consumer_key = consumer_key
    self.consumer_secret = consumer_secret
    self.domain = domain
    self.admin_user = admin_user
    self.admin_pass = admin_pass
    self.max_retries = max_retries
    self.work_queue = work_queue
    self.failure_queue = failure_queue
    self.sig_method = gdata.auth.OAuthSignatureMethod.HMAC_SHA1
    self.email_settings_connection = self._GetEmailSettingsConnection()

  def run(self):
    """Main worker that manages the jobs and applies changes for each user."""

    while True:

      # get task from queue
      task = self.work_queue.get()
      self._ProcessInstruction(task)
      # signals to queue job is done
      self.work_queue.task_done()

  def _ProcessInstruction(self, task):

    # Initialize backoff variables
    backoff = 1  # Start with a one second stall
    backoff_tries = 0

    while True:
      try:
        # Disable IMAP, if user has enabled
        if self._IsImapEnabled(task.GetUserName(),
                               self.email_settings_connection):
          logging.warning('Disabling IMAP for [%s]', task.GetUserName())
          self._DisableImap(task.GetUserName(),
                            self.email_settings_connection)
          SUCCESSFUL_IMAP_DISABLED_USERS.append(task.GetUserName())
        else:
          logging.info('IMAP not enabled for [%s]', task.GetUserName())
          UNCHANGED_IMAP_USERS.append(task.GetUserName())

        # Disable POP, if user has enabled
        if self._IsPopEnabled(task.GetUserName(),
                              self.email_settings_connection):
          logging.warning('Disabling POP for [%s]', task.GetUserName())
          self._DisablePop(task.GetUserName(),
                           self.email_settings_connection)
          SUCCESSFUL_POP_DISABLED_USERS.append(task.GetUserName())
        else:
          logging.info('POP not enabled for [%s]', task.GetUserName())
          UNCHANGED_POP_USERS.append(task.GetUserName())
        return True
      except:
        backoff_tries += 1
        if backoff_tries >= self.max_retries:
          logging.error("""FAILED: Backoff tries exceeded limit of [%s]
                           for user [%s], giving up""",
                        self.max_retries,
                        task.GetUserName())
          return True
        backoff = (2 * backoff)
        logging.warning('Request Failed for user [%s], trying in %d',
                        task.GetUserName(),
                        backoff)
        time.sleep(backoff)

  def _GetEmailSettingsConnection(self):
    client = gdata.apps.emailsettings.client.EmailSettingsClient(
        domain=self.domain)
    client.ClientLogin(email=self.admin_user,
                       password=self.admin_pass,
                       source='imap_policy-python')
    return client

  def _IsImapEnabled(self, input_username, email_settings_conn):
    imap_settings = email_settings_conn.RetrieveImap(username=input_username)
    for c in imap_settings.children:
      if 'name' in c.attributes:
        if c.attributes['name'] == 'enable':
          if c.attributes['value'] == 'false':
            return False
          else:
            return True
        else:
          pass
      else:
        pass
    return False

  def _DisableImap(self, input_username, email_settings_conn):
    email_settings_conn.UpdateImap(username=input_username, enable=False)

  def _IsPopEnabled(self, input_username, email_settings_conn):
    pop_settings = email_settings_conn.RetrievePop(username=input_username)
    for c in pop_settings.children:
      if 'name' in c.attributes:
        if c.attributes['name'] == 'enable':
          if c.attributes['value'] == 'false':
            return False
          else:
            return True
        else:
          pass
      else:
        pass
    return False

  def _DisablePop(self, input_username, email_settings_conn):
    email_settings_conn.UpdatePop(username=input_username, enable=False)


class UserManager(object):
  """Class that builds the list of users that should be audited."""

  def __init__(self, domain, admin_user, admin_pass, exception_group_name):
    self.domain = domain
    self.admin_user = admin_user
    self.admin_pass = admin_pass
    self.exception_group_name = exception_group_name

  def LoadWorkQueue(self, queue):
    """Creates the work queue users eligible to be audited."""

    logging.info('Loading our work queue...')

    # Start with all users
    all_provisioned_users = self._GetAllUsers()

    # Exclude users in authorized Google Group
    if self.exception_group_name:
      # Get list of exception users
      exception_users = self._GetExceptionList()
      unauthorized_imap_users = list(
          set(all_provisioned_users).difference(set(exception_users)))
    else:
      unauthorized_imap_users = all_provisioned_users

    # Add remaining users to work queue
    for unauthorized_imap_user in unauthorized_imap_users:
      logging.info('Adding %s to work queue', unauthorized_imap_user)
      queue.put(WorkerInstruction(unauthorized_imap_user))

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

  def _GetGroupsConnection(self):
    """Gets a Groups Service API connection.

    Returns:
      A Groups Service API ClientLogin connection.
    """

    service = groups_service.GroupsService(email=self.admin_user,
                                           domain=self.domain,
                                           password=self.admin_pass)
    service.ProgrammaticLogin()
    return service

  def _GetExceptionList(self):
    """Method to retrieve members from exception list group."""

    logging.info('Getting members of exception list Google Group...')
    groups_connection = self._GetGroupsConnection()
    exception_users = []
    member_feed = groups_connection.RetrieveAllMembers(
        self.exception_group_name)
    for member in member_feed:
      exception_users.append(member['memberId'].lower())
    return exception_users


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""
  usage = """%prog -k <consumer key> -s <consumer secret>
               -d <domain> -u <admin user> -p <admin password>
              [-g <authorized users group> -t <# threads> -r <max_retries>]"""
  parser = OptionParser(usage=usage)
  parser.add_option('-k', dest='consumer_key',
                    help="""The consumer key.""")
  parser.add_option('-s', dest='consumer_secret',
                    help="""The consumer secret.""")
  parser.add_option('-d', dest='domain',
                    help="""The Google Apps domain.""")
  parser.add_option('-u', dest='admin_user',
                    help="""Admin user for the Provisioning API,
                            e.g. user@domain.com.""")
  parser.add_option('-p', dest='admin_pass',
                    help="""Admin password for the Provisioning API.""")
  parser.add_option('-g', dest='exception_group',
                    help="""Google Group containing users authorized to
                            use IMAP""")
  parser.add_option('-t', dest='threads', default=1, type='int',
                    help="""Number of threads to spawn, max of 100.""")
  parser.add_option('-r', dest='max_retries', default=12, type='int',
                    help="""Maximum number of retries before skipping user.""")

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
  if options.domain is None:
    print '-d (domain) is required'
    invalid_args = True
  if options.admin_user is None:
    print '-u (adminuser@domain.com) is required'
    invalid_args = True
  if options.admin_pass is None:
    print '-p (admin pass) is required'
    invalid_args = True

  if invalid_args:
    sys.exit(4)

  # A check on the MAX_THREAD_VALUE from above
  if options.threads > MAX_THREAD_VALUE:
    logging.info('Threads cannot exceed %d, using %d threads instead of %d',
                 MAX_THREAD_VALUE, MAX_THREAD_VALUE, options.threads)
    options.threads = MAX_THREAD_VALUE

  return options


def main():

  options = ParseInputs()

  start = time.time()

  # Set up logging
  log_filename = ('enforce_imap_policy_%s.log' %
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
                         options.admin_pass,
                         options.exception_group)

  # Load the users eligible for audit into a Queue
  user_mgr.LoadWorkQueue(work_queue)

  # Spawn a pool of threads to process auditing checks
  for i in range(options.threads):
    logging.info('Starting thread: %d', (i + 1))
    t = Worker(options.consumer_key,
               options.consumer_secret,
               options.domain,
               options.admin_user,
               options.admin_pass,
               options.max_retries,
               work_queue,
               failure_queue)
    t.setDaemon(True)
    t.start()

  # wait on the queue until everything has been processed
  work_queue.join()
  # print our stats
  logging.info('============ All Work Queues are Done ============')
  logging.info('Summary Statistics:')
  logging.info('Elapsed Time: %s minutes', (time.time() - start) / 60)
  logging.info('# of users for which IMAP was disabled: %s',
               len(SUCCESSFUL_IMAP_DISABLED_USERS))
  logging.info('# of unchanged IMAP users: %s',
               len(UNCHANGED_IMAP_USERS))
  logging.info('# of users for which POP was disabled: %s',
               len(SUCCESSFUL_POP_DISABLED_USERS))
  logging.info('# of unchanged POP users: %s',
               len(UNCHANGED_POP_USERS))
  logging.info('# of failed users: %s',
               len(FAILED_USERS))

  # print failed users if we had them
  if FAILED_USERS:
    logging.info('failed users: \n%s', FAILED_USERS)
  print 'Log file: %s' % (log_filename)

if __name__ == '__main__':
  main()
