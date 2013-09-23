#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.

"""Given a list of users and a Message ID or Gmail query, moves message(s) to
   a specified label (defaulting to each user's Trash).

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
Given a specific message ID or a Gmail query, this script moves the messages
(using IMAP) to a specified label or, by default, to each user's Trash for all
users listed in the given user_list file. If the message is moved to the Trash,
it can also be automatically purged.

NOTE: IMAP must be turned on for the domain in order to move these messages.

Usage:
imap_email_mover.py [options]

Options:
  -h, --help            show this help message and exit
  --consumer_key=CONSUMER_KEY
                        The OAuth consumer key for the domain. Required.
  --consumer_secret=CONSUMER_SECRET
                        The OAuth consumer secret for the domain. Required.
  --message_id=MESSAGE_ID
                        The message id for the message to move to the trash.
                        Mutually exclusive of --query.
  --query=QUERY
                        A Gmail query to identify messages to be moved.
                        Mutually exclusive of --message_id.
  --user_list=USER_LIST
                        Filename containing a list of users
                        (full email address) that require the message to be
                        moved to the trash. Required.
  --move=[yes|no]
                        Whether to move the messages to the new label (yes) or
                        just add the new label (no). Default is 'no'. If 'yes',
                        a label must be provided.
  --label=LABEL
                        Label to move message(s) to. Default is Gmail's
                        system Trash label. If the label doesn't exist, it will
                        be created.
                        Mutually exclusive of --purge.
  --purge=[yes|no]
                        Whether to permanently purge the message (yes) or
                        not (no). Mutually exclusive of --label.
                        Default is 'no'.

Examples:
  For all users in the user list file, permanently purge all messages sent to
  lawyer@example.domain with the words "privileged" and "confidential" in the
  text.
      imap_email_mover.py --consumer_key='...' --consumer_secret='...' \
          --user_list='...' \
          --query='privileged confidential to:lawyer@example.domain' \
          --purge

  For all users in the user_list file, add a "Litigation" label to any message
  from before January 1st 2012 with the word "litigation" in the subject.
      imap_email_mover.py --consumer_key='...' --consumer_secret='...' \
          --user_list='...' \
          --query='subject:litigation before:2012-01-01' \
          --label='Litigation'

  For all users in the user list file, move all messages in the inbox to the
  "Migrated" label.
      imap_email_mover.py --consumer_key='...' --consumer_secret='...' \
          --user_list='...' \
          --query='in:inbox' \
          --label=Migrated \
          --move=yes
"""

import base64
import csv
import datetime
import hashlib
import hmac
import imaplib
import logging
from optparse import OptionParser
import random
import sys
import time
import urllib


# Modify this variable to the appropriate 'Trash' label. In the U.S., it
# should be 'Trash'. In the U.K. it should be 'Bin'.
_LOCALIZED_TRASH = 'Trash'


class OAuthEntity(object):
  """Represents consumers and tokens in OAuth."""

  def __init__(self, key, secret):
    self.key = key
    self.secret = secret


def EscapeAndJoin(elems):
  return '&'.join([UrlEscape(x) for x in elems])


def FormatUrlParams(params):
  """Formats parameters into a URL query string.

  Args:
    params: A key-value map.

  Returns:
    A URL query string version of the given parameters.
  """
  param_fragments = []
  for param in sorted(params.iteritems(), key=lambda x: x[0]):
    param_fragments.append('%s=%s' % (param[0], UrlEscape(param[1])))
  return '&'.join(param_fragments)


def UrlEscape(text):
  # See OAUTH 5.1 for a definition of which characters need to be escaped.
  return urllib.quote(text, safe='~-._')


def GenerateOauthSignature(base_string, consumer_secret, token_secret=''):
  key = EscapeAndJoin([consumer_secret, token_secret])
  return GenerateHmacSha1Signature(base_string, key)


def GenerateHmacSha1Signature(text, key):
  digest = hmac.new(key, text, hashlib.sha1)
  return base64.b64encode(digest.digest())


def GenerateSignatureBaseString(method, request_url_base, params):
  """Generates an OAuth signature base string.

  Args:
    method: The HTTP request method, e.g. "GET".
    request_url_base: The base of the requested URL. For example, if the
      requested URL is
      "https://mail.google.com/mail/b/xxx@domain.com/imap/?" +
      "xoauth_requestor_id=xxx@domain.com", the request_url_base would be
      "https://mail.google.com/mail/b/xxx@domain.com/imap/".
    params: Key-value map of OAuth parameters, plus any parameters from the
      request URL.

  Returns:
    A signature base string prepared according to the OAuth Spec.
  """
  return EscapeAndJoin([method, request_url_base, FormatUrlParams(params)])


def FillInCommonOauthParams(params, consumer):
  """Fills in parameters that are common to all oauth requests.

  Args:
    params: Parameter map, which will be added to.
    consumer: An OAuthEntity representing the OAuth consumer.
  """

  params['oauth_consumer_key'] = consumer.key
  params['oauth_nonce'] = str(random.randrange(2**64 - 1))
  params['oauth_signature_method'] = 'HMAC-SHA1'
  params['oauth_version'] = '1.0'
  params['oauth_timestamp'] = str(int(time.time()))


def GenerateXOauthString(consumer, xoauth_requestor_id, method, protocol):
  """Generates an IMAP XOAUTH authentication string.

  Args:
    consumer: An OAuthEntity representing the consumer.
    xoauth_requestor_id: The Google Mail user who's inbox will be
                         searched (full email address)
    method: The HTTP method used in the API request
    protocol: The protocol used in the API request

  Returns:
    A string that can be passed as the argument to an IMAP
    "AUTHENTICATE XOAUTH" command after being base64-encoded.
  """

  url_params = {}
  url_params['xoauth_requestor_id'] = xoauth_requestor_id
  oauth_params = {}
  FillInCommonOauthParams(oauth_params, consumer)

  signed_params = oauth_params.copy()
  signed_params.update(url_params)
  request_url_base = (
      'https://mail.google.com/mail/b/%s/%s/' % (xoauth_requestor_id, protocol))
  base_string = GenerateSignatureBaseString(
      method,
      request_url_base,
      signed_params)

  oauth_params['oauth_signature'] = GenerateOauthSignature(base_string,
                                                           consumer.secret)

  # Build list of oauth parameters
  formatted_params = []
  for k, v in sorted(oauth_params.iteritems()):
    formatted_params.append('%s="%s"' % (k, UrlEscape(v)))
  param_list = ','.join(formatted_params)

  # Append URL parameters to request url, if present
  if url_params:
    request_url = '%s?%s' % (request_url_base,
                             FormatUrlParams(url_params))
  else:
    request_url = request_url_base

  return '%s %s %s' % (method, request_url, param_list)


def ImapSearch(user, xoauth_string, message_id, query, move, destination_label,
               purge, imap_debug):
  """Searches the user inbox for a specific message.

  Args:
    user: The Google Mail username that we are searching
    xoauth_string: The authentication string for the aforementioned user
    message_id: The message ID to be searched
    query: A query to find messages
    move: Whether to move the message or just add a label
    destination_label: The label to move the messages to
    purge: Whether to purge the message
    imap_debug: IMAP debug level
  """

  messages_found = 0

  # Setup the IMAP connection and authenticate using OAUTH
  logging.info('[%s] Attempting to login to mailbox', user)
  imap_connection = imaplib.IMAP4_SSL('imap.gmail.com', 993)
  imap_connection.debug = imap_debug
  try:
    imap_connection.authenticate('XOAUTH', lambda x: xoauth_string)
  except imaplib.IMAP4.error:
    logging.error('Error authenticating with OAUTH credentials provideds')
    sys.exit()

  # Attempt to create the destination label. If it already exists, nothing
  # will happen.
  imap_connection.create(destination_label)

  # By default, we want to search for the message in the All Mail folder since
  # all messages live there. IMAP does not allow us to search for a message in
  # the entire mailbox but luckily Gmail has the "All Mail" folder.
  # We also search for the message in the Spam label since spam messages do not
  # show up in All Mail.
  labels = ['[Gmail]/All Mail', '[Gmail]/Spam']

  # Search the labels specified above for the specified message-ID
  for label in labels:
    messages_found = 0
    logging.info('[%s] Searching label %s', user, label)
    imap_connection.select(label)
    #messages_returned = len(data[0])
    #print "%d results returned" % messages_returned

    if message_id is not None:
      search_query = '(HEADER Message-ID "%s")' % message_id
      unused_type, data = imap_connection.uid('SEARCH', None, search_query)
    else:
      unused_type, data = imap_connection.uid('SEARCH', 'X-GM-RAW', query)

    total_in_label = len(data[0].split())
    # For any message that we find, we will copy it to the destination label.
    # and remove the original label. IMAP does not have a move command.
    for num in data[0].split():
      messages_found += 1
      logging.info("[%s] Message #%s (%s of %s):", user, num, messages_found,
                   total_in_label)

      if purge.lower() == 'yes':
        imap_connection.uid('COPY', num, '[Gmail]/' + _LOCALIZED_TRASH)
        imap_connection.expunge()
        logging.info("[%s]   To be purged", user)
      else:
        if move.lower() == 'yes':
          unused_type, label_data = imap_connection.uid('FETCH', num,
                                                        'X-GM-LABELS')
          # Extracting the labels from a text string IMAP result...
          labels = (((label_data[0].split('('))[2].split(')'))[0]).split()
          for label in labels:
            logging.info('[%s]     Removing label: %s', user, label)
            imap_connection.uid('STORE', num, '-X-GM-LABELS', label)
            imap_connection.expunge()

        logging.info('[%s]   Adding label: %s', user, destination_label)
        imap_connection.uid('COPY', num, destination_label)
        imap_connection.expunge()

    logging.info('[%s] Found %s messages(s) in %s', user, messages_found, label)

  if purge.lower() == 'yes':
    label = '[Gmail]/' + _LOCALIZED_TRASH
    imap_connection.select(label)
    messages_found = 0

    if message_id is not None:
      search_query = '(HEADER Message-ID "%s")' % message_id
      unused_type, data = imap_connection.uid('SEARCH', None, search_query)
    else:
      unused_type, data = imap_connection.uid('SEARCH', 'X-GM-RAW', query)

    for num in data[0].split():
      messages_found += 1
      imap_connection.uid('STORE', num, '+FLAGS', '\\Deleted')
      imap_connection.expunge()
      logging.info('[%s] Message has been purged from Gmail', user)
    logging.info('[%s] Total message(s) purged: %s',
                 user, messages_found)
  # Close the connection for the user

  imap_connection.close()
  imap_connection.logout()
  logging.info('[%s] IMAP connection sucessfully closed', user)


def ProcessCSV(input_file):
  """Uses data in CSV file to decide which CRUD function to call.

  This function takes each row from a CSV file and depending on the
  value in the 'action' column calls functions to create, update, or delete
  user accounts.

  Args:
    input_file: [string] filename of CSV file to open.

  Returns:
    Array of users from given input file.
  """

  user_list = []
  row_dict = CSVReader(input_file)
  for row in row_dict:
    user_list.append(row)

  return user_list


def CSVReader(input_file):
  """Creates a CSV DictReader Object.

    The function opens a csv file and sets the first line of the file as\
    headers.  A Dictreader object is then created with these headers.

  Args:
    input_file: [string] filename of CSV file to open.

  Returns:
    DictReader object
  """

  f = open(input_file, 'r')
  reader = csv.reader(f)
  return reader


def GetTimeStamp():
  """Generates a string representing the current time for the log file name.

  Returns:
    A formatted string representing the current date and time.
  """

  now = datetime.datetime.now()
  return now.strftime('%Y%m%d%H%M%S')


def ParseInputs():
  """Interprets command line parameters and checks for required parameters.

  Returns:
    The options object of parsed command line options.
  """

  parser = OptionParser()
  parser.add_option('--consumer_key', dest='consumer_key',
                    help="""The OAuth consumer key for the domain.""")
  parser.add_option('--consumer_secret', dest='consumer_secret',
                    help='The OAuth consumer secret for the domain.')
  parser.add_option('--message_id', dest='message_id',
                    help='The message id for the message to move.')
  parser.add_option('--query', dest='query',
                    help='A Gmail query to identify messages.')
  parser.add_option('--user_list', dest='user_list',
                    help="""Filename containing a list of users
                            (full email address) that require the message to be
                            moved to the trash.""")
  parser.add_option('--move', dest='move', default='no',
                    help="""Whether to move the message (yes) or
                            just add the new label (no). Default is 'no'.""")
  parser.add_option('--label', dest='label', default='[Gmail]/' + _LOCALIZED_TRASH,
                    help='The label to move messages to.')
  parser.add_option('--purge', dest='purge', default='no',
                    help="""Whether to permanently purge the message (yes) or
                            not (no). Default is 'no'.""")

  parser.add_option('--imap_debug_level', dest='imap_debug_level', default=0,
                    help="""[OPTIONAL] Sets the imap debug level.
                            Change this to a higher number to enable console
                            debug""",
                    type='int')

  (options, args) = parser.parse_args()
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))

  invalid_arguments = False
  search_terms = 0

  if options.consumer_key is None:
    print('--consumer_key is required')
    invalid_arguments = True

  if options.consumer_secret is None:
    print('--consumer_secret is required')
    invalid_arguments = True

  if options.user_list is None:
    print('--user_list is required')
    invalid_arguments = True

  if options.message_id is not None:
    search_terms += 1

  if options.query is not None:
    search_terms += 1

  if search_terms == 0:
    print('--message_id or --query is required')
    invalid_arguments = True
  elif search_terms > 1:
    print('use of --message_id and --query are mutually exclusive')
    invalid_arguments = True

  if options.move != 'yes' and options.move != 'no':
    print('--move must be "yes" or "no"')
    invalid_arguments = True

  if options.move == 'yes' and options.label == '[Gmail]/' + _LOCALIZED_TRASH:
    print('--move must have a --label specified that isn\'t "%s"' %
          _LOCALIZED_TRASH)
    invalid_arguments = True

  if options.purge != 'yes' and options.purge != 'no':
    print('--purge must be "yes" or "no"')
    invalid_arguments = True

  if options.label != '[Gmail]/' + _LOCALIZED_TRASH and options.purge != 'no':
    print('--purge can only be used if moving messages to the %s' %
          _LOCALIZED_TRASH)
    invalid_arguments = True

  if invalid_arguments:
    sys.exit(1)

  return options


def main():

  options = ParseInputs()

  # Set up logging
  log_filename = 'imap_email_mover_%s.log' % GetTimeStamp()
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  logging.info('Getting list of users to search for message-id %s from file %s',
               options.message_id, options.user_list)
  for user in ProcessCSV(options.user_list):
    user_email = user[0]
    consumer = OAuthEntity(options.consumer_key, options.consumer_secret)
    xoauth_string = GenerateXOauthString(consumer, user_email, 'GET', 'imap')

    # Run the IMAP search
    ImapSearch(user_email, xoauth_string, options.message_id, options.query,
               options.move, options.label, options.purge,
               options.imap_debug_level)

  print('Log file is: %s' % log_filename)


if __name__ == '__main__':
  main()
