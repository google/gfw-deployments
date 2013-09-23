#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.

"""
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
   THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR
   ITS DERIVATIVES.
   ###########################################################################

   Print out all users in a Domain (uses OAuth 2.0).


Usage: print_users_oauth.py [options]

Options:
  -h, --help        show this help message and exit
  --domain DOMAIN   The target domain.
  --id ID           The OAuth client ID. (Get one in the API console)
  --secret SECRET   The OAuth client secret. (Get one in the API console)
  --refresh_token REFRESH_TOKEN
                    [Optional] The OAuth 2.0 refresh token to use. (to bypass
                        the auth flow)
  --access_token ACCESS_TOKEN
                    [Optional] The OAuth 2.0 access token to use. (to bypass
                        the auth flow)
"""

__author__ = 'hartung@google.com (Justin Hartung)'

from optparse import OptionParser
import sys

import gdata.apps.client
import gdata.apps.organization.client
import gdata.apps.organization.service
import gdata.gauth


# Authorization can be requested for multiple APIs at once by specifying
# multiple scopes separated by # spaces.
SCOPES = ['https://apps-apis.google.com/a/feeds/policies/',
          'https://apps-apis.google.com/a/feeds/user/']


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  parser = OptionParser()
  parser.add_option('--domain', dest='domain',
                    help='The target domain.')
  parser.add_option('--id', dest='oauth_client_id',
                    help='The OAuth client id')
  parser.add_option('--secret', dest='oauth_client_secret',
                    help='The OAuth client secret.')
  parser.add_option('--refresh_token', dest='oauth_refresh_token',
                    help='The OAuth 2.0 refresh token to use.'
                    ' (to bypass the auth flow)')
  parser.add_option('--access_token', dest='oauth_access_token',
                    help='The OAuth 2.0 access token to use.'
                    ' (to bypass the auth flow)')

  (options, args) = parser.parse_args()
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))

  missing_args = False
  if options.domain is None:
    print '--domain is required'
    missing_args = True
  if options.oauth_client_id is None:
    print '--id (client_id) is required'
    missing_args = True
  if options.oauth_client_secret is None:
    print '--secret (client_secret) is required'
    missing_args = True
  if missing_args:
    sys.exit(4)

  return options


def GetOAuthRefreshToken(oauth_client_id, oauth_client_secret):
  """Perform the OAuth 2.0 3 legged flow to get a refresh token."""

  token = gdata.gauth.OAuth2Token(
      client_id=oauth_client_id, client_secret=oauth_client_secret,
      scope=' '.join(SCOPES), user_agent='')

  print 'Go to this URL: ' + token.generate_authorize_url()
  code = raw_input('Copy and paste the code: ')
  # Now with result code, get access + refresh token
  final_token = token.get_access_token(code)
  print 'Refresh token for future use: ' + final_token.refresh_token
  print 'Access_token (good for 3600s): ' + final_token.access_token
  # Return the refresh token
  return final_token.refresh_token


def AuthClient(gd_client, oauth_client_id, oauth_client_secret,
               refresh_token, access_token):
  """Given a refresh token, modifies the client to use the oAuth 2.0 token."""

  token = gdata.gauth.OAuth2Token(
      client_id=oauth_client_id, client_secret=oauth_client_secret,
      scope=' '.join(SCOPES), refresh_token=refresh_token,
      access_token=access_token, user_agent='')
  # Insert the refresh token into the client, which will automatically get a
  # new access token and auth requests
  token.authorize(gd_client)


def main():

  options = ParseInputs()
  domain = options.domain
  oauth_client_id = options.oauth_client_id
  oauth_client_secret = options.oauth_client_secret
  refresh_token = options.oauth_refresh_token
  access_token = options.oauth_access_token

  # Get the client
  gd_client = gdata.apps.client.AppsClient(domain=domain)

  if access_token is None:
    if refresh_token is None:
      refresh_token = GetOAuthRefreshToken(oauth_client_id,
                                           oauth_client_secret)

    print 'Using the refresh token only'
    # Authenticate the client with the refresh token
    AuthClient(gd_client, oauth_client_id, oauth_client_secret,
               refresh_token, access_token='')
  else:
    print 'Using the access and refesh token'
    # Authenticate the client with the access and refresh token
    AuthClient(gd_client, oauth_client_id, oauth_client_secret,
               refresh_token, access_token)

  feed = gd_client.RetrieveAllUsers()
  for entry in feed.entry:
    if entry.login.user_name:
      print 'Username: %s' % entry.login.user_name

if __name__ == '__main__':
  main()