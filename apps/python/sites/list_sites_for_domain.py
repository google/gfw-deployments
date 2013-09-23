#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Dumps group/member data to files that can be used by add_groups_from_csv.py.

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
"""

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'


import gdata.sites.client
import gdata.sites.data
import gdata.auth
from optparse import OptionParser
import sys



def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  parser = OptionParser()
  parser.add_option('-d', dest='domain',
                    help='The domain name to list sotes for.')
  parser.add_option('-u', dest='oauth_requestor_id',
                    help='The admin user to use for authentication.')
  parser.add_option('-k', dest='oauth_consumer_key',
                    help="The OAuth consumer key")
  parser.add_option('-s', dest='oauth_consumer_secret',
                    help='The The OAuth consumer secret.')

  (options, args) = parser.parse_args()
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))

  if options.domain is None:
    print '-d (domain) is required'
    sys.exit(1)
  if options.oauth_requestor_id is None:
    print '-u (admin user) is required'
    sys.exit(1)
  if options.oauth_consumer_key is None:
    print '-k (consumer_key) is required'
    sys.exit(1)
  if options.oauth_consumer_secret is None:
    print '-s (consumer_secret) is required'
    sys.exit(1)

  return options


def GetConnection(options):

  CONSUMER_KEY = options.oauth_consumer_key
  CONSUMER_SECRET = options.oauth_consumer_secret
  SIG_METHOD = gdata.auth.OAuthSignatureMethod.HMAC_SHA1
  requestor_id = options.oauth_requestor_id
  sites_domain = options.domain

  two_legged_oauth_token = gdata.gauth.TwoLeggedOAuthHmacToken(CONSUMER_KEY, CONSUMER_SECRET, requestor_id)

  gd_client = gdata.sites.client.SitesClient(source='sites_list', domain=sites_domain)
  gd_client.auth_token = two_legged_oauth_token
  gd_client.ssl = True
  return gd_client


def main():

  options = ParseInputs()

  gd_client = GetConnection(options)

  # Get Sites for the domain
  uri = '%s?include-all-sites=%s&max-results=100' % (gd_client.MakeSiteFeedUri(), 'true')
  feed = gd_client.GetSiteFeed(uri=uri)

  for entry in feed.entry:
       print "Site Title:[%s]" % entry.title.text
       print "Site URL:[%s]" % entry.GetAlternateLink().href
       feed = gd_client.GetAclFeed(uri=entry.FindAclLink())

       # Get ACLs for site
       print "Site ACLs:"
       for acl in feed.entry:
         print '\t%s (%s) - %s' % (acl.scope.value, acl.scope.type, acl.role.value)
       print "\n"


if __name__ == '__main__':
  main()
