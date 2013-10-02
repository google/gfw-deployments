#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Sample script to demonstrate the Admin SDK API.

Usage:
  $ python report_api.py

You can also get help on all the command-line flags the program understands
by running:

  $ python report_api.py --help
"""

__author__ = 'Andrew Luong <aluong@google.com>'

import argparse
import datetime
import json
import logging
from logging import handlers
import os
import sys

import httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>
CLIENT_SECRETS = 'client_secrets.json'

# Helpful message to display in the browser if the CLIENT_SECRETS file
# is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console <https://code.google.com/apis/console>.

""" % os.path.join(os.path.dirname(__file__), CLIENT_SECRETS)


class PathError(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)


def SetDate():
  date = raw_input("Please enter date YYYY-MM-DD i.g. '2013-05-16'\n")
  return date


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  parser = argparse.ArgumentParser(description='Process flags passed to script')
  parser.add_argument('-m', '--mode', dest='mode',
                      help='customer_usage')
  parser.add_argument('-l', '--logging',
                      help='enable logging')
  parser.add_argument('-e', '--email', dest='email',
                      help='The email of a user')
  parser.add_argument('-i', '--input', dest='user_csv',
                      help='The user input file name')
  parser.add_argument('-f', '--logfile', dest='log_file',
                      default='./report_logging', help='The log file name')
  parser.add_argument('-d', '--debug', dest='debug',
                      help='Set logging level to debug')
  parser.add_argument('-v', '--verbose', dest='verbose', default=False,
                      action='store_true', help='Verbose logging to console')
  args = parser.parse_args()

  return parser, args


def ConfigureLogger(logfile, debug=False, stdout_logging=False):
  """Configure the logging facility and starts logging.

  Args:
    logfile: A string containing the name of file to write log data to.
    debug: A boolean indicating if the debug logging level is set.
    stdout_logging: A boolean indicating that log events are written to console.

  Returns:
    log: An instance of the logging object.
  """
  log = logging.getLogger('NetworkTesting')
  # Disable logging to console
  log.propagate = False

  date_tag = datetime.datetime.now().strftime('%Y-%b-%d_%H-%M-%S')
  log_file = '%s%s.log' % (logfile, date_tag)
  loggingformat = '%(asctime)s %(levelname)s %(process)d %(lineno)d %(message)s'
  formatter = logging.Formatter(loggingformat)

  # Verify that the logging directory exists and set a log rotation
  if not os.path.exists(os.path.dirname(log_file)):
    raise PathError('log directory does not exist (%s)' %
                    os.path.dirname(log_file))
    sys.exit(1)

  handler_file = logging.handlers.RotatingFileHandler(log_file,
                                                      maxBytes=25600,
                                                      backupCount=5)
  handler_file.setFormatter(formatter)
  handler_stdout = logging.StreamHandler(sys.stdout)

  if debug:
    log.setLevel(logging.DEBUG)
    print 'Log Level is DEBUG\n'

  else:
    log.setLevel(logging.INFO)
    print 'Log Level is INFO\n'

  if stdout_logging:
    print 'Standard output logging enabled\n'
    log.propagate = True
    log.addHandler(handler_file)
    log.addHandler(handler_stdout)
  else:
    log.addHandler(handler_file)

  return log


def main(argv):

  parser, args = ParseInputs()
  # print args
  if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

  date = SetDate()
  filename = 'usage_report_%s.csv' % (date)
  outfile = open(filename, 'w')
  # httplib2.debuglevel=4

  # Logging
  log = ConfigureLogger(args.log_file, args.debug, args.verbose)

  # OAUTH
  oauth_scope = 'https://www.googleapis.com/auth/admin.reports.usage.readonly'
  flow = flow_from_clientsecrets(CLIENT_SECRETS, scope=oauth_scope,
                                 message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage('report.dat')
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    print 'invalid credentials'
    # Save the credentials in storage to be used in subsequent runs.
    credentials = run(flow, storage)

  http = httplib2.Http()
  http = credentials.authorize(http)

  # Envoke calls to request reports for customer_usage or user_usage
  url_list = []

  if args.mode == 'customer_usage':
    url = 'https://www.googleapis.com/admin/reports/v1/usage/dates/%s' % (date)
    url_list.append(url)
    log.info(('Url: %s') % (url))

  elif args.user_csv:
    email_list = open(args.user_csv, 'r').readlines()
    for email in email_list:
      url = 'https://www.googleapis.com/admin/reports/v1/usage/users/'
      url += url + '%s/dates/%s' % (email.rstrip(), date)
      url_list.append(url)

  elif args.email:
    url = ('https://www.googleapis.com/admin/reports/v1/usage/users/%s/dates/%s'
           % (args.email, date))
    url_list.append(url)

  elif args.email is None:
    print 'Give the email id for the user'
  else:
    print 'No more args'

  # Loop through each user usage reuqest
  count = 0
  csv_header = []
  for url in url_list:
    csv_row = []
    response, content = http.request(url)
    jsondata = json.loads(content)
    reports = jsondata['usageReports']
    params = reports[0]['parameters']

    if  'error' in jsondata.keys():
      log.info(('Http response: %s ') % response)
      log.info(('Error: %s ') % jsondata['error']['message'])

    if args.mode == 'customer_usage':
      log.info(('Http response: %s ') % response)
      log.info(('Http content: %s ') % content)
      # TODO(aluong) add all uses report api call whee nextPageToken is relevant
      # log.info(('Http content nextPageToken: %s ')
      #           % jsondata['nextPageToken'])

    else:
      user_email = reports[0]['entity']['userEmail']
      csv_header.append('userEmail')
      csv_row.append(user_email)

    try:
      if args.mode == 'customer_usage':
        csv_row = ['n/a', 'n/a', 'n/a']
      auth_apps = []
      for i in params:
        name = i[i.keys()[1]]
        val = i[i.keys()[0]]
        if name == 'accounts:authorized_apps':
          name = ('authorized_apps_client_name, authorized_apps_client_id,'
                  'authorized_apps_num_users')
          for app in val:
            approw = []
            approw.append(str(app['client_name']))
            approw.append(str(app['client_id']))
            approw.append(str(app['num_users']))
            auth_apps.append(approw)

        else:
          csv_row.append(str(val))

        if count == 0:
          csv_header.append(name.replace(':', '_'))

      if count == 0:
        outfile.write(', '.join(csv_header))
        outfile.write('\n')

      outfile.write(','.join(csv_row))
      outfile.write('\n')
      for app in auth_apps:
        outfile.write(', '.join(app))
        outfile.write('\n')

      outfile.write('\n')
      count += 1
    except KeyError, e:
      log.info('Error %s -- URL %s' %(e, url))

if __name__ == '__main__':
  main(sys.argv)
