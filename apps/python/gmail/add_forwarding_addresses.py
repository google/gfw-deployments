#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.

"""Script to apply forwarding addresses based on inupt file.


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

Usage: add_forwarding_addresses.py -d <domain>
              -u <admin user> -p <admin password>
              -i <input_file>
              [-t <# threads> -r <max_retries>]

Options:
  -h, --help      show this help message and exit
  -d DOMAIN       The Google Apps domain.
  -u ADMIN_USER   Admin user for the Provisioning API,
                  e.g. user@domain.com.
  -p ADMIN_PASS   Admin password for the Provisioning API.
  -i INPUT_FILE   Input file containing forwarding mappings..
  -t THREADS      Number of threads to spawn, max of 100.
  -r MAX_RETRIES  Maximum number of retries before skipping user.

Input file should be a CSV with two columns where the first column
is the user's email address and the second is the forwarding address
to forward mail to.  The first line must have the following headers:
 - user_email_address,forwarding_address


"""


__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import csv
import datetime
import logging
from optparse import OptionParser
import Queue
import re
import sys
import threading
import time

import gdata.apps.emailsettings.client


# A arbitrary ceiling to the number of threads
# that can be started.
MAX_THREAD_VALUE = 100

# Array of failed mappings
FAILED_MAPPINGS = []
# Succesfully applied forwardings
SUCCESSFUL_FORWARDS = []
# Skipped Records
SKIPPED_RECORDS = []


class WorkerInstruction(object):
  """Class to hold instructions for updating email settings."""

  def __init__(self, user_email_address, forwarding_address):
    self.user_email_address = user_email_address
    self.forwarding_address = forwarding_address

  def __str__(self):
    return ('WorkerInstruction{User:[%s], ForwardTo:[%s]}' %
            (self.user_email_address, self.forwarding_address))

  def GetUser(self):
    return self.user_email_address

  def GetForwardingAddress(self):
    return self.forwarding_address


class Worker(threading.Thread):
  """Threaded worker."""

  def __init__(self, domain, admin_user, admin_pass, max_retries,
               work_queue, failure_queue):
    threading.Thread.__init__(self)
    self.domain = domain
    self.admin_user = admin_user
    self.admin_pass = admin_pass
    self.max_retries = max_retries
    self.work_queue = work_queue
    self.failure_queue = failure_queue
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
        # Add forwarding addres
        self._AddForward(self.email_settings_connection, task.GetUser(),
                         task.GetForwardingAddress())
        SUCCESSFUL_FORWARDS.append(task.GetUser() + '->' +
                                   task.GetForwardingAddress())
        return True
      except Exception as e:
        backoff_tries += 1
        if backoff_tries >= self.max_retries:
          logging.error("""FAILED: Backoff tries exceeded limit of [%s]
                           for user [%s] forwarding to [%s], giving up""",
                        self.max_retries,
                        task.GetUser(),
                        task.GetForwardingAddress())
          FAILED_MAPPINGS.append(task.GetUser() + '->' +
                                 task.GetForwardingAddress())
          return True
        backoff = (2 * backoff)
        logging.warning('Request Failed for [%s] forward to [%s],'
                        'trying again in %d:%s',
                        task.GetUser(),
                        task.GetForwardingAddress(),
                        backoff,
                        str(e))
        time.sleep(backoff)

  def _GetEmailSettingsConnection(self):
    client = gdata.apps.emailsettings.client.EmailSettingsClient(
        domain=self.domain)
    client.ClientLogin(email=self.admin_user,
                       password=self.admin_pass,
                       source='add-forwarding-python')
    return client

  def _AddForward(self, client, user_email_address, forward_to):
    logging.info('Adding forwarding to %s from %s',
                 forward_to, user_email_address)
    client.UpdateForwarding(username=user_email_address, enable=True,
                            forward_to=forward_to, action='KEEP')


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""
  usage = """%prog -d <domain> -u <admin user> -p <admin password>
               -i <input_file>
              [-t <# threads> -r <max_retries>]"""
  parser = OptionParser(usage=usage)
  parser.add_option('-d', dest='domain',
                    help="""The Google Apps domain.""")
  parser.add_option('-u', dest='admin_user',
                    help="""Admin user for the Provisioning API,
                            e.g. user@domain.com.""")
  parser.add_option('-p', dest='admin_pass',
                    help="""Admin password for the Provisioning API.""")
  parser.add_option('-i', dest='input_file',
                    help="""Input file containing forwarding mappings..""")
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
  if options.domain is None:
    print '-d (domain) is required'
    invalid_args = True
  if options.admin_user is None:
    print '-u (adminuser@domain.com) is required'
    invalid_args = True
  if options.admin_pass is None:
    print '-p (admin pass) is required'
    invalid_args = True
  if options.input_file is None:
    print '-i (input_file) is required'
    invalid_args = True

  if invalid_args:
    sys.exit(4)

  # A check on the MAX_THREAD_VALUE from above
  if options.threads > MAX_THREAD_VALUE:
    logging.info('Threads cannot exceed %d, using %d threads instead of %d',
                 MAX_THREAD_VALUE, MAX_THREAD_VALUE, options.threads)
    options.threads = MAX_THREAD_VALUE

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
  """Validates the input file contents."""

  row_dict = CSVReader(input_file)

  headers = row_dict.fieldnames
  if headers[0] != 'user_email_address':
    print 'First column must contain header "user_email_address"'
    sys.exit(1)
  if headers[1] != 'forwarding_address':
    print 'First column must contain header "forwarding_address"'
    sys.exit(1)


def main():

  options = ParseInputs()
  ValidateInputFile(options.input_file)

  start = time.time()

  # Set up logging
  log_filename = ('add_forwarding_addresses_%s.log' %
                  (datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  work_queue = Queue.Queue()
  failure_queue = Queue.Queue()

  records = CSVReader(options.input_file)

  for record in records:
    # TODO(mdauphinee): Determine if this check is necessary
    #if not re.search('@' + options.domain + '$', record['user_email_address']):
    #  logging.error("Skipping [%s] forwarding to [%s]: " +
    #                "Input user_email_address not in correct domain",
    #                record['user_email_address'], record['forwarding_address'])
    #  SKIPPED_RECORDS.append(record['user_email_address'])
    #  continue
    logging.info('Adding %s forwards to %s to the work queue',
                 record['user_email_address'].lower(),
                 record['forwarding_address'].lower())
    work_queue.put(WorkerInstruction(record['user_email_address'],
                                     record['forwarding_address']))

  # Spawn a pool of threads to process auditing checks
  for i in range(options.threads):
    logging.info('Starting thread: %d', (i + 1))
    t = Worker(options.domain,
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
  logging.info('============ All Work Is Done ============')
  logging.info('Summary Statistics:')
  logging.info('Elapsed Time: %s minutes', (time.time() - start) / 60)
  logging.info('# of forwards applied: %s',
               len(SUCCESSFUL_FORWARDS))
  logging.info('# of failed forwards: %s',
               len(FAILED_MAPPINGS))
  logging.info('# of skipped records: %s',
               len(SKIPPED_RECORDS))

  # print failed users if we had them
  if FAILED_MAPPINGS:
    logging.info('failed mappings: \n%s', FAILED_MAPPINGS)
  print 'Log file: %s' % (log_filename)

if __name__ == '__main__':
  main()
