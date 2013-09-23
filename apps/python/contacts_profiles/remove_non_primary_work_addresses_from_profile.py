#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Removes all non-primary work addresses from the profiles.

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

  Usage: remove_non_primary_work_addresses_from_profile.py [options]

  Options:
    -h, --help            show this help message and exit
    -d DOMAIN             Domain
    -u ADMIN_USER         Admin user
    -p ADMIN_PASS         Admin password
    --profile_to_change=PROFILE_TO_CHANGE
                          OPTIONAL:a single username (without domain) to search.
                          Otherwise this will search all profiles.
    -a                    Unless this flag is present, this runs
                          in a Dry Run mode making no changes

"""


__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import datetime
import logging
from optparse import OptionParser
import sys

import gdata.apps.service as apps_service
import gdata.contacts
import gdata.contacts.service


def ParseInputs():
  parser = OptionParser()
  parser.add_option('-d', dest='domain',
                    help="""Domain""")
  parser.add_option('-u', dest='admin_user',
                    help="""Admin user""")
  parser.add_option('-p', dest='admin_pass',
                    help="""Admin password""")
  parser.add_option('--profile_to_change', dest='profile_to_change',
                    help="""OPTIONAL:Single username (without domain) to search.
                            Otherwise this will search all profiles.""")
  parser.add_option('-a', dest='apply', action='store_true', default=False,
                    help="""Unless this flag is present, this runs
                            in a Dry Run mode making no changes""")

  (options, args) = parser.parse_args()

  # series of if's to check our flags
  invalid_args = False
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))
  if not options:
    parser.print_help()
    invalid_args = True
  if options.domain is None:
    print '-d (domain) is required'
    invalid_args = True
  if options.admin_user is None:
    print '-u (adminuser@domain.com) is required'
    invalid_args = True
  if options.admin_pass is None:
    print '-p (admin pass) is required'
    invalid_args = True

  if invalid_args:
    sys.exit(3)

  return options


def GetContactsConnection(user, password, domain):
  gd_client = gdata.contacts.service.ContactsService(
      contact_list=domain)
  gd_client.email = user
  gd_client.password = password
  gd_client.source = 'Remove-Non-Primary-Work-Addresses-Python-1'
  gd_client.ProgrammaticLogin()

  return gd_client


def GetProvConnection(user, password, domain):
  service = apps_service.AppsService(email=user,
                                     domain=domain,
                                     password=password)
  service.ProgrammaticLogin()
  return service


def IsWorkAddress(structured_postal_address):
  schema_name = 'http://schemas.google.com/g/2005#work'
  return structured_postal_address.rel == schema_name


def IsPrimaryAddress(structured_postal_address):
  return structured_postal_address.primary == 'true'


def main():

  options = ParseInputs()

  # Set up logging
  log_filename = ('remove_non_primary_work_addresses_from_profile_%s.log' %
                  (datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  if not options.apply:
    logging.info('RUNNING IN DRY RUN MODE, NO CHANGES WILL BE MADE')

  con_conn = GetContactsConnection(options.admin_user,
                                   options.admin_pass,
                                   options.domain)
  prov_conn = GetProvConnection(options.admin_user,
                                options.admin_pass,
                                options.domain)

  # Define User List
  users = []
  if options.profile_to_change:
    users.append(options.profile_to_change)
  else:
    user_feed = prov_conn.RetrieveAllUsers()
    for user_entry in user_feed.entry:
      users.append(user_entry.login.user_name)

  for u in users:

    entry_uri = con_conn.GetFeedUri(kind='profiles',
                                    projection='full')
    entry_uri += '/' + u + '?v=3.0'
    logging.info(entry_uri)
    entry = con_conn.GetProfile(entry_uri)

    needs_update = False

    # Remove any organization external IDs added
    external_id_list = []
    if len(entry.external_id) > 0:
      for ext_id in entry.external_id:
        if ext_id.rel and ext_id.rel.lower() == 'organization':
          logging.info('User has External ID [%s] populated for rel [%s].  Clearing',
                       str(ext_id.value), str(ext_id.rel))
          needs_update = True
        else:
          external_id_list.append(ext_id)

    entry.external_id = external_id_list

    # Remove non-primary work address
    address_list = []
    for a in entry.structured_postal_address:
      if IsWorkAddress(a) and not IsPrimaryAddress(a):
        logging.info('Excluding work address [%s]', a)
        needs_update = True
      else:
        address_list.append(a)

    entry.structured_postal_address = address_list

    if needs_update:
      if options.apply:
        logging.info('Updating Profile')
        con_conn.UpdateProfile(edit_uri=entry.GetEditLink().href,
                               updated_profile=entry)
      else:
        logging.info('Would have updated profile')
    else:
      logging.info('No update to profile required')

  print 'Log file: %s' % (log_filename)


if __name__ == '__main__':
  main()
