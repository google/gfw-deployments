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

"""Scan existing groups for groups with external accessibility enabled.

This script is intended for domains that have chosen to select
"Public on the Internet" as the domain-wide setting for the highest level of
access to groups for users outside the domain, yet want to monitor which Groups
have been given external view or post permissions.

The script logs these Warnings to an output file for review.

Usage:
  - Create a file with the OAuth 2.0 credentials in JSON format similar to the
    following:

{
  "installed": {
    "client_id": "123456789.apps.googleusercontent.com",
    "client_secret":"KWJ43490JKKJbkjbyETlupEk",
    "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://accounts.google.com/o/oauth2/token"
  }
}

  - Run: python monitor_externally_available_groups.py [-d domain -f conf_file]

  - For more help run: ./monitor_externally_available_groups.py --help

Requirements:
 - google-api-python-client:
      Run: sudo easy_install --upgrade google-api-python-client
"""

__author__ = 'Matthew Dauphinee <mdauphinee@google.com>'

import datetime
import logging
import sys

from apiclient.discovery import build
import gdata.apps.groups.client
import gflags
import httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

FLAGS = gflags.FLAGS

gflags.DEFINE_string('domain', None,
                     """Primary domain of Apps account to scan.
                        Will prompt at the command line if not provided.""",
                     short_name='d')
gflags.DEFINE_string('oauth2_conf_file', 'client_secrets.json',
                     """The configuration file containing the credentials
                        in JSON format.""")
gflags.DEFINE_string('scopes',
                     ('https://apps-apis.google.com/a/feeds/groups/ '
                      'https://www.googleapis.com/auth/apps.groups.settings'),
                     'A comma separated list of the scopes being requested.')

# TODO(mdauphinee):Add ability to provide a list of authorized exceptions.
# TODO(mdauphinee):Add ability to send warnings to an email address.


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
                                  user_agent='monitor-groups-sample')
  return token


def GetGroupSettings(http, group_id):
  """Retrieve the Group's Settings.

  Args:
    http: httplib2.Http authorized object
    group_id: The ID for a specific group

  Returns:
    g: an object containing the Groups Settings
  """

  service = build('groupssettings', 'v1', http=http)
  # Get the resource 'group' from the set of resources of the API.
  group_resource = service.groups()

  # Retrieve the group properties
  g = group_resource.get(groupUniqueId=group_id).execute()

  return g


def GetProvisioningClient(credentials, domain, scopes):
  """Create an OAuth 2.0 token for use with the GData client library."""

  oauth2token = GetOAuth2Token(credentials.client_id,
                               credentials.client_secret,
                               scopes,
                               credentials.access_token,
                               credentials.refresh_token)
  groups_client = oauth2token.authorize(
      gdata.apps.groups.client.GroupsProvisioningClient(domain=domain))

  return groups_client


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
  log_prefix = 'monitor_externally_available_groups'
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

  # Get Provisioning API client
  prov_client = GetProvisioningClient(credentials, FLAGS.domain,
                                      FLAGS.scopes)

  # Iterate over all groups
  logging.info('Retrieving all groups in the Apps account')
  for entry in prov_client.RetrieveAllGroups().entry:
    logging.info('Checking %s', entry.group_id)

    pgs = GetGroupSettings(http, entry.group_id)

    if pgs['whoCanViewGroup'] == 'ANYONE_CAN_VIEW':
      logging.warning(("Group [%s]: Any Internet user can VIEW the group's "
                       "messages."), entry.group_id)

    if pgs['whoCanPostMessage'] == 'ANYONE_CAN_POST':
      logging.warning(('Group [%s]: Any Internet user who is outside your '
                       'account can access your Google Groups service and '
                       'POST a message.'), entry.group_id)

  logging.info('Groups check complete.\n\n')
  logging.info('To review warnings that were detected, run:')
  logging.info('\tgrep WARNING %s', log_filename)


if __name__ == '__main__':

  # Assuming the user will run this headless on a remote machine
  FLAGS.auth_local_webserver = False

  main(sys.argv)
