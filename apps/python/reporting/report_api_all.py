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

"""Sample for the Group Settings API demonstrates get and update method.

Usage:
  $ python reportapi.py

You can also get help on all the command-line flags the program understands
by running:

  $ python reportapi.py --help
"""

__author__ = 'Andrew Luong <aluong@google.com>'

from optparse import OptionParser
import os
import datetime
import logging
from logging import handlers
import pprint
import sys
import json
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

def setDate():
  date = raw_input("Please enter date YYYY-MM-DD i.g. '2013-05-16'\n")
  return date

def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""
  usage = 'usage: %prog [options]'
  parser = OptionParser(usage=usage)
  parser.add_option('--emailId',
                    help='email address')
  parser.add_option('--mode',
                    help='all_users')
  parser.add_option('--logging',
                    help='enable logging')
  parser.add_option('-i', dest='user_csv',
                    help="""The user input file name""")
  parser.add_option('-l', dest='log_file', default='./report_logging',
                    help="""The log file name""")
  parser.add_option('-d', dest='debug',
                    help="""Set logging level to debug""")
  parser.add_option('-v', dest='verbose',default=False, action='store_true',
                    help="""Enable verbose logging to console""")
  (options, args) = parser.parse_args()

  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))

  return options


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
  #Disable logging to console
  log.propagate = False

  date_tag = datetime.datetime.now().strftime('%Y-%b-%d_%H-%M-%S')
  log_file = '%s%s.log' % (logfile, date_tag)
  loggingformat = '%(asctime)s %(levelname)s %(process)d %(lineno)d %(message)s'
  formatter = logging.Formatter(loggingformat)

  # Verify that the logging directory exists and set a log rotation
  if not os.path.exists(os.path.dirname(log_file)):
    raise Exception, ('log directory does not exist (%s)' %
                      os.path.dirname(log_file))
    sys.exit(1)  #TODO(mpedersen): Instead of exiting, log to the the console.

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
  """Demos the setting of the access properties by the Reports API."""
  outfile = open("report_output.csv" , 'w')
  print outfile
  #httplib2.debuglevel=4
  usage = 'usage: %prog [options]'

  options=ParseInputs()

  # Logging
  log = ConfigureLogger(options.log_file, options.debug, options.verbose)

  #OAUTH 
  FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
  #scope='https://www.googleapis.com/auth/admin.reports.usage.readonly,https://www.googleapis.com/auth/apps.reports.audit.readonly,https://www.googleapis.com/auth/admin.directory.user',
  scope='https://www.googleapis.com/auth/admin.reports.usage.readonly',
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage('report.dat')
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    print 'invalid credentials'
    # Save the credentials in storage to be used in subsequent runs.
    credentials = run(FLOW, storage)

  http = httplib2.Http()
  http = credentials.authorize(http)


  url_list = []
  date = setDate()

  if options.mode=='all_users':
    #url = 'https://www.googleapis.com/apps/reports/v1/usage/users/all/dates/%s?&maxResults=1' % (date) 
    url = 'https://www.googleapis.com/admin/reports/v1/usage/dates/%s' % (date) 
    url_list.append(url)
    log.info(('Url: %s') % url )
 
  elif options.user_csv:
      email_list = open(options.user_csv, 'r').readlines()
      for email in email_list:
        print 'Email is: %s' % (email)
        url = 'https://www.googleapis.com/apps/reports/v1/usage/users/%s/dates/%s' % (email.rstrip(), date)
        url_list.append(url)
  elif options.emailId:
      url = 'https://www.googleapis.com/apps/reports/v1/usage/users/%s/dates/%s' % (options.emailId, date)
      url_list.append(url)
      
  else:
    if options.emailId is None:
      print 'Give the email id for the user'
     
  
  #Loop through urls
  count = 0 
  for url in url_list:
    #print 'The URL is: %s' % (url)
    response, content  = http.request(url)
    jsondata = json.loads(content)
    #if  jsondata['error']:
    if  'error' in jsondata.keys():
      print 'Error message  %s' % (jsondata['error']['message'])
      log.info(('Http response: %s ') % response)
      log.info(('Error: %s ') % jsondata['error']['message'])
    if options.mode=='all_users': 
       log.info(('Http response: %s ') % response)
       log.info(('Http content: %s ') % content)
       log.info(('Http content nextPageToken: %s ') % jsondata['nextPageToken'])
   
    try:
      reports=jsondata['usageReports']
      params=reports[0]['parameters']
      csv_header = []
      csv_row = [] 
      csv_data = []
      for i in params:
        name = i[i.keys()[1]]
        val = i[i.keys()[0]]
        #print "%s === %s" % (name, valname)
        if count==0:
          csv_header.append(name)
        csv_row.append(str(val))
   
  
      #write to file
      if count==0:
        outfile.write(','.join(csv_header))
        outfile.write('\n')
      outfile.write(','.join(csv_row))
      outfile.write('\n')
      count +=1
    except KeyError,e: 
     #print 'Error %s with user/url %s' % (e, url)
     log.info('Error %s -- URL %s' %(e, url))

  #for key, value in content.iteritems():
  #  print key, value

if __name__ == '__main__':
  main(sys.argv)
