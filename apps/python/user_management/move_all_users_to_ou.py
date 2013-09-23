#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

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

   Moves *all* users from the given domain to the given OU (in path form)
   
   NOTE: OU must be in "path" form.

Usage: move_all_users_to_ou.py [options]

Options:
  -h, --help     show this help message and exit
  -d DOMAIN      Moves all users in this domain.
  -u ADMIN_USER  admin user.
  -p ADMIN_PASS  admin pass
  -f ORG         From Org in path form
  -t ORG         To Org in path form
  -l             If present will list Orgs in the domain
  --apply        Script makes no changes unless --apply is presented

  Either give [-f and -t] or -l, but not both

"""

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import datetime
import gdata.apps.organization.service
import gdata.apps.service as apps_service
from optparse import OptionParser
import logging
import sys


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  parser = OptionParser()
  parser.add_option('-d', dest='domain',
                    help='Moves all users in this domain.')
  parser.add_option('-u', dest='admin_user',
                    help='admin user.')
  parser.add_option('-p', dest='admin_pass',
                    help="admin pass")
  parser.add_option('-f', dest='from_org',
                    help="From org in path form")
  parser.add_option('-t', dest='to_org',
                    help="To org in path form")
  parser.add_option('-l', dest='list_ou', action="store_true",
                    default=False,
                    help="If present will list Orgs in the domain")
  parser.add_option('--apply', dest="apply", action="store_true",
                    default=False, help="Script makes no changes unless --apply is presented")


  (options, args) = parser.parse_args()
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))

  if options.domain is None:
    print '-d (domain) is required'
    sys.exit(1)
  if options.admin_user is None:
    print '-u (admin user) is required'
    sys.exit(1)
  if options.admin_pass is None:
    print '-p (admin_ass) is required'
    sys.exit(1)
  if options.from_org is None and options.to_org and options.list_ou is None:
    print 'Either [-f/-t] or -l (list) is required'
    sys.exit(1)
  if (options.from_org is None and options.to_org is not None) or (options.from_org is not None and options.to_org is None):
    print 'Both -f and -t need to be present'
    sys.exit(1)

  return options


def GetConnection(options):

  organization_client = gdata.apps.organization.service.OrganizationService(
      email=options.admin_user, domain=options.domain, password=options.admin_pass,
      source='Move Users Org Utility')
  organization_client.ProgrammaticLogin()
  return organization_client


def GetAllUsers(domain, options):
  users = []
  connect = apps_service.AppsService(email=options.admin_user,
                                     domain=options.domain,
                                     password=options.admin_pass)
  connect.ProgrammaticLogin()
  logging.info('Pulling user list')
  user_feed = connect.RetrieveAllUsers()
  user_feed.entry[0]
  for user_entry in user_feed.entry:
    users.append(user_entry.login.user_name.lower())
  return users


def UserInFromOrg(gd_client, customer_id, user_email, from_org):
  users_org = gd_client.RetrieveOrgUser(customer_id, user_email)
  return users_org['orgUnitPath'] == from_org


def main():

  options = ParseInputs()


  # Set up logging
  log_filename = ('move_all_users_to_ou_%s.log' %
                  (datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  gd_client = GetConnection(options)
  customer_id = gd_client.RetrieveCustomerId()["customerId"]

  if options.list_ou:
    logging.info("Listing OUs for domain [%s]", options.domain)
    orgs = gd_client.RetrieveAllOrgUnits(customer_id)
    for org in orgs:
      logging.info("Org Name: [%s] Org Path: [%s]", org['name'], org['orgUnitPath'])
    sys.exit(2)

  users = GetAllUsers(options.domain, options)

  if not options.apply:
    logging.info("RUNNING IN DRY RUN MODE, NO CHANGES BEING APPLIED")

  for user in users:
    user_email = "%s@%s" % (user, options.domain)
    if UserInFromOrg(gd_client, customer_id, user_email, options.from_org):
      if options.apply:
        logging.info("Moving user [%s] to OU [%s]", user_email, options.to_org)
        gd_client.MoveUserToOrgUnit(customer_id,
                                    org_unit_path=options.to_org,
                                    users_to_move=[user_email])
      else:
        logging.info("DRY RUN: Would have moved user [%s] to OU [%s]", user_email, options.to_org)
    else:
      logging.info("User: [%s] not in from Org: [%s]", user_email, options.from_org)

if __name__ == '__main__':
  main()
