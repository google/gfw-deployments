#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.

"""Given a user and an optional query, exports message(s) to Drive

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

NOTE: IMAP must be turned on for the domain in order to move these messages.

Usage:
imap_to_drive.py [options]

Options:
  -h, --help            Show this help message and exit.
  --key=CONSUMER_KEY
                        The OAuth consumer key for the domain. Required.
  --secret=CONSUMER_SECRET
                        The OAuth consumer secret for the domain. Required.
  --user=EMAIL_ADDRESS
                        The email address of the user to be exported. Required.
  --owner=EMAIL_ADDRESS
                        The email address of the user to own the Drive archive.
                        Optional. Will default to the specified user.
  --query=QUERY
                        A Gmail query to identify messages to be exported.
                        Optional. By default, all messages will be exported.
  --truncate_label=LABEL
                        A Gmail label to add to any messages that were
                        truncated when pushed to Drive.
"""

import base64
from datetime import datetime
import gdata.docs.client as docs_client
import gdata.gauth
import hashlib
import hmac
import imaplib
import logging
from optparse import OptionParser
import random
import re
import StringIO
import sys
import time
import urllib

# The maximum seconds to sustain an open connection to each of the services
# we rely on
DOCS_CONNECTION_MAX_LENGTH = 306
IMAP_CONNECTION_MAX_LENGTH = 300

# The number of bytes of RFC822 message to stick in Google Drive
EMAIL_TRUNCATE_BYTES = 256000


class OAuthEntity(object):
  """Represents consumers and tokens in OAuth."""

  def __init__(self, key, secret):
    """ Initializes an OAuthEntity

    Arguments:
      key: a string, the OAuth key
      secret: a string, the OAuth secret
    """
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


def GenerateOauthSignature(base_string, secret, token_secret=''):
  key = EscapeAndJoin([secret, token_secret])
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

def GetHeaderFromMessage(message, header):
  tag_length = len(header) + 2

  try:
    value = (re.search(header + ': .*[\r\n]', message).group(0))[tag_length:]
  except Exception, e:
    value = ''

  return value.strip()

# Keeps track of all processed Message-IDs in order to detect duplication
processed_messages = []
def ExportLabelToFolder(imap_connection, docs_connection, label, query, owner):
  """ Exports all messages under an IMAP label to a comparable Drive folder.

  Arguments:
    imap_connection: an imaplib connection, the connection to IMAP
    docs_connection: a gdata.docs.client.DocsClient, the connection to Google
                     Drive
    label: a string, the IMAP label from which to export messages
    query: a Gmail-style query to restrict the export of messages. (None means
           to export all messages.)
    owner: a string, the email address of the person who should own the export

  Returns:
    Nothing
  """
  # Grab references to all of the messages in a label
  message_locators = imap_connection.GetMessageLocatorsInLabel(label, query)

  total_in_label = len(message_locators)

  if message_locators:
    docs_connection.CreateFolder(label, owner, docs_connection.folder)

    message_count = 0
    for message_locator in message_locators:
      message_count += 1
      message = imap_connection.GetMessage(message_locator)

      if not message:
        logging.info('%s:   %s of %s: Could not retrieve message.',
                     datetime.now(), message_count, total_in_label)
        continue

      sender_full = GetHeaderFromMessage(message, 'From')

      if not sender_full:
        sender_full = GetHeaderFromMessage(message, 'Sender')

        if not sender_full:
          sender_full = '<unknown_user@unknown_domain>'

      try:
        sender = re.search("[A-Za-z0-9\'\-\+\._]*@[A-Za-z0-9\-\.]*",
                           sender_full).group(0).strip()
      except Exception, e:
        sender = 'unknown_sender'

      subject = GetHeaderFromMessage(message, 'Subject')

      if not subject:
        subject = 'unknown_subject'

      message_id = GetHeaderFromMessage(message, 'Message-ID')

      if message_id in processed_messages:
        message = 'Duplicate message with Message ID: ' + message_id
        logging.info('%s:     The following message is a duplicate:',
                     datetime.now())
      else:
        if message_id:
          processed_messages.append(message_id)

      title = sender + ": " + subject

      if docs_connection.CreateDoc(title, message, owner):
        imap_connection.AddTruncationLabel(message_locator)

      logging.info('%s:   %s of %s: Added "%s" to collection %s',
                   datetime.now(), message_count, total_in_label,
                   title, docs_connection.folder.name)

    docs_connection.FolderComplete()


class XOAuthInfo(object):
  def __init__(self, user, key, secret):
    self.user = user
    self.key = key
    self.secret = secret


class IMAPConnection(object):
  def __init__(self, xoauth, truncate_label=None, imap_debug=0):
    self.xoauth = xoauth
    self.truncate_label = truncate_label
    self.imap_debug = imap_debug
    self.connection = None
    self.connection_start = datetime(1, 1, 1)
    self.label = None

  def _Connect(self):
    logging.info('%s: Attempting IMAP login: %s', datetime.now(),
                 self.xoauth.user)

    self.connection_start = datetime.now()
    self.connection = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    self.connection.debug = self.imap_debug

    consumer = OAuthEntity(self.xoauth.key, self.xoauth.secret)
    xoauth_string = GenerateXOauthString(consumer, self.xoauth.user, 'GET',
                                         'imap')

    try:
      self.connection.authenticate('XOAUTH', lambda x: xoauth_string)
    except Exception, e:
      logging.error('%s: Error authenticating with OAUTH credentials provided '
                    '[%s]', datetime.now(), str(e))

    logging.info('%s: Logged in to IMAP', datetime.now())

    if self.label:
      self.connection.select(self.label)

  def Close(self):
    try:
      self.connection.close()
      self.connection.logout()
      logging.info('%s: Logged out', datetime.now())
    except Exception, e:
      self.connection = None

  def _CheckRefresh(self):
    if ((datetime.now() - self.connection_start).seconds >
        IMAP_CONNECTION_MAX_LENGTH):
      logging.info('%s:     Refreshing IMAP connection',
                   datetime.now())
      self.Close()
      self._Connect()

  def AddTruncationLabel(self, message_locator):
    if self.truncate_label:
      logging.info('%s:     Label "%s" added.', datetime.now(),
                   self.truncate_label)
      self.connection.create(self.truncate_label)
      self.connection.uid('COPY', message_locator, self.truncate_label)
      self.connection.expunge()

  def GetMessageLocatorsInLabel(self, label, query):
    self._CheckRefresh()

    try:
      (result, unused_data) = self.connection.select(label)
    except Exception, e:
      logging.info('%s: Skipping label: %s', datetime.now(), label)
      return []
 
    logging.info('%s: Processing label: %s', datetime.now(), label)
    self.label = label

    unused_type, data = self.connection.uid('SEARCH', 'X-GM-RAW', query)

    return data[0].split()

  def List(self):
    self._CheckRefresh()

    try:
      (unused_data, list) = self.connection.list()
    except Exception, e:
      list = []

    return list
    
  def GetMessage(self, message_locator):
    self._CheckRefresh()

    remaining_tries = 4
    while remaining_tries >= 0:
      try:
        (result, message_info) = self.connection.uid('FETCH', message_locator,
                                                     '(RFC822)')

        remaining_tries = -1
      except Exception, e:
        if remaining_tries == 0:
          return ''
        remaining_tries -= 1
        time.sleep(3)
        logging.info('%s:     Re-establishing IMAP connection',
                     datetime.now())
        self.Close()
        self._Connect()

    message = ''
    if message_info:
      try:
        (unused_data, message) = message_info[0]
      except Exception, e:
        return ''

    return message


class Folder(object):
  def __init__(self, connection, name, owner=None, parent=None):
    self.name = name
    self.owner = owner
    self.parent = parent

    parent_folder = None
    if parent:
      parent_folder = self.parent.folder

    document = gdata.docs.data.Resource(type='folder', title=self.name)
    self.folder = connection.CreateResource(document,
                             collection=parent_folder)

    if self.owner:
      acl_entry = gdata.docs.data.AclEntry(
          scope=gdata.acl.data.AclScope(value=self.owner, type='user'),
          role=gdata.acl.data.AclRole(value='owner'),)

      connection.AddAclEntry(self.folder, acl_entry, send_notifications=False)

    self.uri = self.folder.GetSelfLink().href

  def Reconnect(self, connection):
    self.folder = connection.GetResourceBySelfLink(self.uri)

    if self.parent:
      self.parent.Reconnect(connection)
  

class DocsConnection(object):
  def __init__(self, xoauth):
    self.xoauth = xoauth
    self.connection = None
    self.connection_start = datetime(1, 1, 1)

    self.folder = None

  def _Connect(self):
    logging.info('%s: Attempting Drive login', datetime.now())
    self.connection = docs_client.DocsClient(source='docs_meta-v1')
    self.connection_start = datetime.now()
    self.connection.auth_token = gdata.gauth.TwoLeggedOAuthHmacToken(
        self.xoauth.key, self.xoauth.secret, self.xoauth.user)

  def Close(self):
    del(self.connection)
    self.connection = None

  def _CheckRefresh(self):
    if ((datetime.now() - self.connection_start).seconds >
        DOCS_CONNECTION_MAX_LENGTH):
      logging.info('%s:     Refreshing Drive connection',
                   datetime.now())
      self.Close()
      self._Connect()

      if self.folder:
        self.folder.Reconnect(self.connection)

  def CreateFolder(self, name, owner=None, parent=None):
    """ Creates and assigns ownership of a Drive Collection

    Arguments:
      name: a string, the name of the collection
      owner: the owner of the collection. (None means don't set an ACL)
      parent: the parent collection. (None means use the document root)
    """
    self._CheckRefresh()

    self.folder = Folder(self.connection, name, owner, parent)

  def FolderComplete(self):
    self.folder = self.folder.parent

  def CreateDoc(self, name, content, owner=None):
    self._CheckRefresh()

    truncated = False
    remaining_tries = 4
    while remaining_tries >= 0:
      document_reference = gdata.docs.data.Resource(type='document', title=name)
      if len(content) > EMAIL_TRUNCATE_BYTES:
        logging.info('%s:     The following message was truncated: %s bytes',
                     datetime.now(), len(content))
        content = content[:EMAIL_TRUNCATE_BYTES]
        truncated = True
      media = gdata.data.MediaSource(file_handle=StringIO.StringIO(content),
                                     content_type='text/plain',
                                     content_length=len(content))

      try:
        document = self.connection.CreateResource(document_reference,
            media=media, collection=self.folder.folder)

        remaining_tries = -2
      except Exception, e:
        logging.info('%s:     Re-establishing Docs connection',
                     datetime.now())
        self.Close()
        self._Connect()

        remaining_tries -= 1

    if remaining_tries == -2 and owner:
      acl_entry = gdata.docs.data.AclEntry(
          scope=gdata.acl.data.AclScope(value=owner, type='user'),
          role=gdata.acl.data.AclRole(value='owner'),)

      self.connection.AddAclEntry(document, acl_entry, send_notifications=False)

    return truncated

def ImapSearch(user, xoauth, owner, query, truncate_label, imap_debug):
  """Searches the user inbox for specific messages. Uploads them to Drive.

  Args:
    user: The Google Mail username that we are searching
    xoauth: An XOAuthInfo object, the credentials to establish XOAuth 
    owner: The owner of the uploaded Drive files
    query: A query to find messages
    imap_debug: IMAP debug level
  """

  messages_found = 0

  # Setup the Drive connection and authenticate using OAUTH
  docs_connection = DocsConnection(xoauth)

  export_folder_name = user + ' exported ' + GetTimeStamp()
  docs_connection.CreateFolder(export_folder_name, owner)

  imap_connection = IMAPConnection(xoauth, truncate_label, imap_debug)

  labels = []
  label_list = imap_connection.List()

  for label_info in label_list:
    label_data = label_info.split('"')
    metadata = label_data[0]
    label = label_data[3]

    if metadata.find('\\Noselect') != -1:
      continue

    labels.append(label)

  for label in labels:
    ExportLabelToFolder(imap_connection, docs_connection, label, query, owner)
    
  logging.info('%s: Processing complete.', datetime.now())


def GetTimeStamp():
  """Generates a string representing the current time for the log file name.

  Returns:
    A formatted string representing the current date and time.
  """
  now = datetime.now()
  return now.strftime('%Y.%m.%d@%H:%M:%S')


def ParseInputs():
  """Interprets command line parameters and checks for required parameters.

  Returns:
    The options object of parsed command line options.
  """

  parser = OptionParser()
  parser.add_option('--key', dest='key',
                    help='The OAuth consumer key for the domain.')
  parser.add_option('--secret', dest='secret',
                    help='The OAuth consumer secret for the domain.')
  parser.add_option('--user', dest='user',
                    help='The Email address of the user to export.')
  parser.add_option('--owner', dest='owner',
                    help='The new owner of the archive in Drive.')
  parser.add_option('--query', dest='query', default='',
                    help='A Gmail query to identify messages.')
  parser.add_option('--truncate_label', dest='trunacte_label', default=None,
                    help='A Gmail label to add to truncated messages.')

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

  if options.key is None:
    print '--key is required'
    invalid_arguments = True

  if options.secret is None:
    print '--secret is required'
    invalid_arguments = True

  if options.user is None:
    print '--user is required'
    invalid_arguments = True

  if invalid_arguments:
    sys.exit(1)

  return options


def main():
  options = ParseInputs()

  # Set up logging
  log_filename = 'imap_to_drive_%s.log' % GetTimeStamp()
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  xoauth = XOAuthInfo(options.user, options.key, options.secret)

  ImapSearch(options.user, xoauth, options.owner, options.query,
             options.trunacte_label, options.imap_debug_level)

  print 'Log file is: %s' % log_filename


if __name__ == '__main__':
  main()
