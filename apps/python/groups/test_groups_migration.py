#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.
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
###########################################################################
# DISCLAIMER:
#
# (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
# WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
# WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND
#
# (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
# OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
# DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
# GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
# THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR ITS
# DERIVATIVES.
###########################################################################

"""Migrates a single message to the Groups Migration API.

Requirements:
 - google-api-python-client:
      Run: sudo easy_install --upgrade google-api-python-client

Example:
  ./test_groups_migration.py -m message.txt \
                             -d mdauphinee.info \
                             -g accounting@mdauphinee.info
"""

__author__ = 'Matthew Dauphinee <mdauphinee@google.com>'

import datetime
import logging
import sys

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
import gdata.apps.groups.client
import gflags
import httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

FLAGS = gflags.FLAGS

gflags.DEFINE_string('domain', None,
                     """Primary domain of Apps account.
                        Will prompt at the command line if not provided.""",
                     short_name='d')
gflags.DEFINE_string('group_id', None,
                     'The group to migrate the sample message to.',
                     short_name='g')
gflags.DEFINE_string('message_file', None,
                     'The file containing the RFC2822 formatted message.',
                     short_name='m')
gflags.DEFINE_string('oauth2_conf_file', 'client_secrets.json',
                     """The configuration file containing the credentials
                        in JSON format.""")
gflags.DEFINE_string('scopes',
                     'https://www.googleapis.com/auth/apps.groups.migration',
                     'A comma separated list of the scopes being requested.')

gflags.MarkFlagAsRequired('message_file')


def GetCredentials(oauth2_conf_file, scopes):
  """Request a token for the scopes provided."""

  flow = flow_from_clientsecrets(oauth2_conf_file,
                                 scope=scopes)

  storage = Storage('group.dat')
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    print 'Credentials are invalid or do not exist.'
    credentials = run(flow, storage)

  return credentials


def GetHttpObject(credentials):
  """Create an httplib2.Http object for HTTP requests and authorize it."""
  http = httplib2.Http()
  http = credentials.authorize(http)

  return http


def GetOAuth2Token(client_id, client_secret, scopes,
                   access_token, refresh_token):
  """Get the OAuth 2.0 token to be used with the Provisioning API.

  Args:
    client_id: String client_id of the installed application
    client_secret: String client_secret of the installed application
    scopes: String containing desired scopes of access
    access_token: String access token obtained from OAuth 2.0 server flow
    refresh_token: String refresh token obtained with access token

  Returns:
    token: String OAuth 2.0 token adapted for the Groups Provisioning API.
  """
  token = gdata.gauth.OAuth2Token(client_id=client_id,
                                  client_secret=client_secret,
                                  scope=scopes,
                                  access_token=access_token,
                                  refresh_token=refresh_token,
                                  user_agent='groups-migration-sample')
  return token


def GetTimeStamp():
  """Return a formatted timestamp of now."""

  now = datetime.datetime.now()
  return now.strftime('%Y%m%d%H%M%S')


def main(argv):

  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  if FLAGS.domain is None:
    FLAGS.domain = raw_input('Enter the domain: ')

  # Set up logging
  log_prefix = 'test_groups_migration_'
  log_filename = '%s_%s_%s.log' % (log_prefix, FLAGS.domain, GetTimeStamp())
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  # Get authentication objects
  credentials = GetCredentials(FLAGS.oauth2_conf_file, FLAGS.scopes)
  http = GetHttpObject(credentials)

  service = build('groupsmigration', 'v1', http=http)
  grp_mig_resource = service.archive()

  media = MediaFileUpload(FLAGS.message_file, mimetype='message/rfc822')
  response = grp_mig_resource.insert(groupId=FLAGS.group_id,
                                     media_body=media).execute()

  logging.info('Response Code: %s', response['responseCode'])

if __name__ == '__main__':

  # Assuming the user will run this headless on a remote machine
  FLAGS.auth_local_webserver = False

  main(sys.argv)
