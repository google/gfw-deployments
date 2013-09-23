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

"""Scan existing groups for potential configuration issues.

This scripts attempts to raise awareness to configurations that may
result in unintended outcomes.  The two main issues it addresses are:
 - Nested Groups configured more restrictively than parent groups, thus
   potentially resulting in undelivered mail
 - Innapropriate Groups moderation configurations based on "who can post"

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

  - Run: python analyze_groups_config.py [-d domain -f conf_file]

  - For more help run: ./analyze_groups_config.py --help

Requirements:
 - google-api-python-client:
      Run: sudo easy_install --upgrade google-api-python-client
"""

__author__ = 'Matthew Dauphinee <mdauphinee@google.com>'

import datetime
import logging
from sets import Set
import sys

from apiclient.discovery import build
import gdata.apps.groups.client
import gdata.apps.groups.service
import gflags
import httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

FLAGS = gflags.FLAGS

gflags.DEFINE_string('admin_user', None,
                     'Email address of admin account.',
                     short_name='u')
gflags.DEFINE_string('admin_pass', None,
                     'Password of admin account.',
                     short_name='p')
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


gflags.MarkFlagAsRequired('admin_user')
gflags.MarkFlagAsRequired('admin_pass')


def GetGroupsServiceConnection(admin_user, admin_pass, domain):
  groups_client = gdata.apps.groups.service.GroupsService(email=admin_user,
                                                          domain=domain,
                                                          password=admin_pass,
                                                          source='GroupsClient "Unit" Tests')
  groups_client.ProgrammaticLogin()
  return groups_client


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
                                  user_agent='analyze-groups-sample')
  return token


def GetGroupSettings(http, group_id):
  """Retrieve the Group's Settings.

  Args:
    http: httplib2.Http autrized object
    group_id: The ID for a specific group

  Returns:
    g: an object containing the Groups Settings
  """

  service = build('groupssettings', 'v1', http=http)
  # Get the resource 'group' from the set of resources of the API.
  group_resource = service.groups()

  # Retrieve the group properties
  g = group_resource.get(groupUniqueId=group_id).execute()

  # print '\nRetrieved settings for group\n'
  # pprint.pprint(g)

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


def GetUserMemberList(group_id, prov_client):
  """Retrieves all non-Group members in a Group's membership."""

  all_members = prov_client.RetrieveAllMembers(group_id)

  user_members = []

  for member in all_members.entry:

    # Skip group members
    if member.member_type != 'Group':
      user_members.append(member.member_id)

  return user_members


def main(argv):

  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  if FLAGS.domain is None:
    FLAGS.domain = raw_input('Enter the domain: ')

  # Set up logging
  log_filename = 'analyze_groups_config_%s_%s.log' % (FLAGS.domain,
                                                      GetTimeStamp())
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

  # Get Groups Service connection
  groups_service = GetGroupsServiceConnection(FLAGS.admin_user, FLAGS.admin_pass, FLAGS.domain)

  # Iterate over all groups
  for entry in prov_client.RetrieveAllGroups().entry:
    logging.info('Checking %s', entry.group_id)

    pgs = GetGroupSettings(http, entry.group_id)

    # Check moderation settings for externally postable groups
    if pgs['whoCanPostMessage'] == 'ANYONE_CAN_POST':
      if pgs['spamModerationLevel'] == 'ALLOW':
        logging.warning(('Group %s is set to %s for whoCanPostMessage, '
                         'but no spam moderation is being performed (%s)'),
                        entry.group_id,
                        pgs['whoCanPostMessage'],
                        pgs['spamModerationLevel'])
      if pgs['messageModerationLevel'] != 'MODERATE_NON_MEMBERS':
        logging.warning(('Group %s is set to %s for whoCanPostMessage. '
                         'messageModerationLevel is recommended to be set '
                         'to MODERATE_NON_MEMBERS to protect the group from '
                         'spam (currently set to %s)'),
                        entry.group_id, pgs['whoCanPostMessage'],
                        pgs['messageModerationLevel'])

    # Look for Nested Groups
    members = prov_client.RetrieveAllMembers(entry.group_id)
    for member in members.entry:
      if member.member_type == 'Group':


        # Check if nested Group is an Owner.  Discouraged practice.
        if (groups_service.IsOwner(member.member_id, entry.group_id)):
          logging.warning('Member %s of Group %s is a Group which is marked as '
                          'an Owner', member.member_id, entry.group_id)

        cgs = GetGroupSettings(http, member.member_id)

        logging.debug('Parent who can post: %s',
                      pgs['whoCanPostMessage'])
        logging.debug('Child who can post: %s',
                      cgs['whoCanPostMessage'])

        if (cgs['whoCanPostMessage'] == 'NONE_CAN_POST' and
            pgs['whoCanPostMessage'] != 'NONE_CAN_POST'):
          logging.warning(('Child group %s set to %s, '
                           'but parent group %s set to %s'),
                          member.member_id, cgs['whoCanPostMessage'],
                          entry.group_id, pgs['whoCanPostMessage'])

        if pgs['whoCanPostMessage'] == 'ANYONE_CAN_POST':
          # Make sure child group allows anyone to post
          if cgs['whoCanPostMessage'] != 'ANYONE_CAN_POST':
            logging.warning(('Parent Group %s set to ANYONE_CAN_POST, '
                             'but child group %s is not (%s)'),
                            entry.group_id, member.member_id,
                            cgs['whoCanPostMessage'])

        elif pgs['whoCanPostMessage'] == 'ALL_IN_DOMAIN_CAN_POST':
          if (cgs['whoCanPostMessage'] == 'ALL_MANAGERS_CAN_POST' or
              cgs['whoCanPostMessage'] == 'ALL_MEMBERS_CAN_POST'):
            logging.warning(('Parent group %s set to ALL_IN_DOMAIN_CAN_POST '
                             'but child group %s is set to %s'),
                            entry.group_id, member.member_id,
                            cgs['whoCanPostMessage'])
        elif pgs['whoCanPostMessage'] == 'ALL_MANAGERS_CAN_POST':
          if (cgs['whoCanPostMessage'] == 'ALL_MEMBERS_CAN_POST' or
              cgs['whoCanPostMessage'] == 'ALL_MANAGERS_CAN_POST'):
            logging.warning(('Parent group %s set to %s, but child group %s '
                             'set to %s.  Ensure these lists match.'),
                            entry.group_id, pgs['whoCanPostMessage'],
                            member.member_id, cgs['whoCanPostMessage'])
        elif pgs['whoCanPostMessage'] == 'ALL_MEMBERS_CAN_POST':
          if cgs['whoCanPostMessage'] == 'ALL_IN_DOMAIN_CAN_POST':
            logging.warning(('Parent group %s set to %s and child group %s '
                             'is set to %s'),
                            entry.group_id, pgs['whoCanPostMessage'],
                            member.member_id, cgs['whoCanPostMessage'])
          elif cgs['whoCanPostMessage'] == 'ALL_MANAGERS_CAN_POST':
            logging.warning(('Parent group %s set to %s and child group %s '
                             'is set to %s'),
                            entry.group_id, pgs['whoCanPostMessage'],
                            member.member_id, cgs['whoCanPostMessage'])
          elif cgs['whoCanPostMessage'] == 'ALL_MEMBERS_CAN_POST':
            parent_users = Set(GetUserMemberList(entry.group_id, prov_client))
            child_users = Set(GetUserMemberList(member.member_id, prov_client))
            if parent_users.difference(child_users):
              logging.warning(('Parent group %s set to %s and Child group %s '
                               'set to %s, but members of %s are not members '
                               'of %s'),
                              entry.group_id, pgs['whoCanPostMessage'],
                              member.member_id, cgs['whoCanPostMessage'],
                              entry.group_id, member.member_id)

  logging.info('Groups analyzation complete.\n\n')
  logging.info('To review warnings that were detected, run:')
  logging.info('\tgrep WARNING %s', log_filename)


if __name__ == '__main__':

  # Assuming the user will run this headless on a remote machine
  FLAGS.auth_local_webserver = False

  main(sys.argv)

