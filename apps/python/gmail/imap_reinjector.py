#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.
"""
  imap_reinjector.py

DESCRIPTION:
  Queries a Gmail account (via IMAP) for messages that need to be re-delivered.
  This tool is useful in an instance where a Google Apps Email Setting is
  inadvertently used to re-route messages into a single user's mailbox, for
  example by using an overly-agressive content filter that redirects matching
  messages to an admin or role mailbox.

DEPENDENCIES:
  Use of this tool requires a supplementary Python library to handle XOAuth
  authentication and authorization. This library can be found at:
    https://code.google.com/p/enterprise-deployments/source/browse/trunk/
        apps/python/lib/XOAuth.py

  Use of this tool requires a supplementary Python library to manage an IMAP
  connection. This library can be found at:
    https://code.google.com/p/enterprise-deployments/source/browse/trunk/
        apps/python/lib/IMAPConnection.py

  Use of this tool requires a supplementary Python library to manage threading
  of IMAP connections. This library can be found at:
    https://code.google.com/p/enterprise-deployments/source/browse/trunk/
        apps/python/lib/Threading.py

LICENSING:
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

DISCLAIMER:
  ###########################################################################

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

NOTE:
  IMAP must be turned on for the domain in order to move these messages.

USAGE:
  imap_reinjector.py [options]

  Options:
    -h, --help            Show this help message and exit
    --consumer_key=CONSUMER_KEY
                          The OAuth consumer key for the domain. Required
    --consumer_secret=CONSUMER_SECRET
                          The OAuth consumer secret for the domain. Required
    --user=EMAIL_ADDRESS
                          Email address of user of messages to reinject
    --query=QUERY
                          A Gmail query to identify messages to be reinjected
    --restrict_domains_list=FILE
                          A file containing a list of domains to limit
                          reinjection to
    --completed_label=LABEL
                          A Gmail label to add reinjected messages to.
    --remove_from_subject=STRING
                          A text string to remove from the subject lines of
                          retransmitted messages
    --threads=NUMBER
                          The number of concurrent IMAP connections to attempt

EXAMPLES:
"""

import datetime
import logging
import re
import smtplib
import sys

from email.parser import Parser
#    https://code.google.com/p/enterprise-deployments/source/browse/trunk/
#        apps/python/gmail/IMAPConnection.py
from IMAPConnection import IMAPConnection
from optparse import OptionParser
#    https://code.google.com/p/enterprise-deployments/source/browse/trunk/
#        apps/python/lib/Threading.py
from Threading import Threading
#    https://code.google.com/p/enterprise-deployments/source/browse/trunk/
#        apps/python/lib/XOAuth.py
from XOAuth import XOAuth

def ReinjectMessage(thread_number=0, item={}, metadata={}):
  """Reinjects a message to aspmx.l.google.com

  Args:
    thread_number: The number/id of the processing thread
    item: A dictionary containing information specific to the item being
        processed
    metadata: A dictionary containing information about all items being
        processed

  Returns:
    True - if the message is reinjected
    False - if the message could not be reinjected
  """
  locator = item['locator']
  message_number = item['message_number']

  message_count = metadata['message_count']
  xoauth_string = metadata['xoauth_string']
  imap_debug = metadata['imap_debug']
  restrict_domains = metadata['restrict_domains']
  remove_from_subject = metadata['remove_from_subject']
  label = metadata['label']
  query = metadata['query']
  completed_label = metadata['completed_label']

  try:
    imap_connection = IMAPConnection(xoauth_string=xoauth_string,
                                     imap_debug=imap_debug)
  except:
    return False

  try:
    imap_connection.GetMessageLocatorsInLabel(label, query)
  except:
    return False

  logging.info('Thread #%s - Fetching message #%s of %s (%s).',
               thread_number, message_number, message_count, locator)
  try:
    message = imap_connection.GetMessage(locator)
  except:
    return False

  headers = Parser().parsestr(message)

  if headers['From']:
    sender = re.findall('[a-z0-9\.\-\+\']*@[a-z0-9\.]*',
                     headers['From'].lower())
  elif headers['Sender']:
    sender = re.findall('[a-z0-9\.\-\+\']*@[a-z0-9\.]*',
                     headers['Sender'].lower())
  
  addresses = []
  if headers['To']:
    addresses.extend(re.findall('[a-z0-9\.\-\+\']*@[a-z0-9\.]*',
                     headers['To'].lower()))
  if headers['Cc']:
    addresses.extend(re.findall('[a-z0-9\.\-\+\']*@[a-z0-9\.]*',
                     headers['Cc'].lower()))
  if headers['X-Forwarded-To']:
    addresses.extend(re.findall('[a-z0-9\.\-\+\']*@[a-z0-9\.]*',
                     headers['X-Forwarded-To'].lower()))

  groups = re.findall('received: by .* '
                      'for <[a-z0-9\.\-\+\']*@[a-z0-9\.]*>;',
                      message.lower())
  for group in groups:
    addresses.extend(re.findall('[a-z0-9\.\-\+\']*@[a-z0-9\.]*', group))

  if restrict_domains:
    new_addresses = []
    for address in addresses:
      for domain in restrict_domains:
        if address[0 - len(domain):] == domain:
          new_addresses.append(address)

    addresses = new_addresses

  if addresses:
    if remove_from_subject:
      if headers['Subject'].find(remove_from_subject) == 0:
        message = re.sub('Subject: %s' % remove_from_subject, 'Subject: ',
                         message)
        new_headers = Parser().parsestr(message)

    logging.info('  Thread #%s - Reinjecting message #%s.' % (thread_number,
                                                              message_number))
    smtp_connection = smtplib.SMTP('aspmx.l.google.com')
    smtp_connection.sendmail(sender, addresses, message)
    smtp_connection.quit()

    if completed_label:
      imap_connection.AddLabel(locator, completed_label)
  else:
    logging.info('  No acceptable addresses to reinject to. Skipping.')

  imap_connection.Close()

  return True


def ImapSearch(xoauth_string, query, restrict_domains_file='',
               completed_label='', remove_from_subject='', threads=1,
               imap_debug=0):
  """Searches an inbox for certain messages and queues each one for reinjection

  Args:
    xoauth_string: An authentication string
    query: A query to find messages
    restrict_domains_file: A filename, the contents of which will be used to
        restrict addresses to which a message should be reinjected to only
        a certain set of domains
    completed_label: A string containing the label to add to processed messages
    remove_from_subject: A string that should be removed from the beginning of
        each subject line if it exists
    threads: An integer; the number of IMAP connections to establish
        simultaneously
    imap_debug: IMAP debug level

  Raises:
    An IOException if the restrict_domains_file can't be opened.
  """
  imap_connection = IMAPConnection(xoauth_string=xoauth_string,
                                   imap_debug=imap_debug)
  if completed_label:
    imap_connection.CreateLabel(completed_label)
  imap_connection.Close()

  restrict_domains = []
  if restrict_domains_file:
    try:
      domains_file = open(restrict_domains_file, 'r')
    except Exception, e:
      raise

    domains = domains_file.readlines()
    domains_file.close()

    for domain in domains:
      restrict_domains.append(domain.rstrip())

  labels = ['[Gmail]/All Mail', '[Gmail]/Spam']

  for label in labels:
    metadata = {'label': label,
                'query': query,
                'xoauth_string': xoauth_string,
                'imap_debug': imap_debug,
                'restrict_domains': restrict_domains,
                'remove_from_subject': remove_from_subject,
                'completed_label': completed_label}

    imap_connection = IMAPConnection(xoauth_string=xoauth_string,
                                     imap_debug=imap_debug)
    locators = imap_connection.GetMessageLocatorsInLabel(label, query)
    imap_connection.Close()

    metadata['message_count'] = len(locators)
    logging.info('Found %s messages matching query \'%s\' in %s',
                 metadata['message_count'], query, label)

    items = []
    message_number = 0
    for locator in locators:
      message_number += 1
      items.append({'locator': locator, 'message_number': message_number})

    Threading(items, function=ReinjectMessage, metadata=metadata,
              threads=threads, debug_level=1)


def ParseInputs():
  """Interprets command line parameters and checks for required parameters.

  Returns:
    The options object of parsed command line options.
  """

  parser = OptionParser()
  parser.add_option('--consumer_key', dest='consumer_key',
                    help='The OAuth consumer key for the domain')
  parser.add_option('--consumer_secret', dest='consumer_secret',
                    help='The OAuth consumer secret for the domain')
  parser.add_option('--user', dest='user',
                    help='The email address of the user to reinject messages')
  parser.add_option('--query', dest='query',
                    help='A Gmail query to identify messages for reinjection')
  parser.add_option('--restrict_domains_file', dest='restrict_domains_file',
                    help='A file containing a list of domains to restrict '
                    'reinjection to')
  parser.add_option('--completed_label', dest='completed_label',
                    help='A label to add to all reinjected messages')
  parser.add_option('--remove_from_subject', dest='remove_from_subject',
                    help='Text to remove from the subject header')
  parser.add_option('--threads', dest='threads', default=1,
                    help='The number of IMAP connections to open. Default = 1'
                    'simultaneously', type='int')
  parser.add_option('--imap_debug_level', dest='imap_debug_level', default=0,
                    help='[OPTIONAL] Sets the imap debug level\n'
                    '   Change this to a higher number to enable console debug',
                    type='int')

  (options, args) = parser.parse_args()
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))

  invalid_arguments = False
  search_terms = 0

  if options.consumer_key is None:
    print '--consumer_key is required'
    invalid_arguments = True

  if options.consumer_secret is None:
    print '--consumer_secret is required'
    invalid_arguments = True

  if options.user is None:
    print '--user is required'
    invalid_arguments = True

  if options.query is None:
    print '--query is required'
    invalid_arguments = True

  if invalid_arguments:
    sys.exit(1)

  return options


def main():
  options = ParseInputs()

  # Set up logging
  log_filename = 'imap_reinjector-%s.log' % (
      datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  xoauth = XOAuth(options.consumer_key, options.consumer_secret)
  xoauth_string = xoauth.GetXOAuthString(options.user, 'GET', 'imap')

  # Run the IMAP search
  ImapSearch(xoauth_string, options.query, options.restrict_domains_file,
             options.completed_label, options.remove_from_subject,
             int(options.threads), options.imap_debug_level)

  print 'Log file is: %s' % log_filename


if __name__ == '__main__':
  main()
