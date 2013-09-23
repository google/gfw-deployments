#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.

"""Re-orders the phone numbers in profiles.

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

  Usage: profile_phone_reorder.py [options]

  Prior to running this tool, please review (and alter) the order of the
  priority preference for each type of phone entry in the PHONE_ORDER list
  in the program (below).

  Options:
    -h, --help            show this help message and exit
    -d DOMAIN             Domain
    -u ADMIN_USER         Admin user
    -p ADMIN_PASS_FILE    OPTIONAL: A file containing only the admin password
                          otherwise there will be a prompt for the admin
                          password.
                          Make sure this file is properly secured!
    -l LIST_OF_PROFILES_TO_CHANGE
                          OPTIONAL: A comma-separated list of usernames
                          (without domain) to search otherwise this will
                          search all profiles.
    -a                    Unless this flag is present, this runs
                          in a Dry Run mode making no changes

"""

__author__ = ['mdauphinee@google.com (Matt Dauphinee)',
              'gbloom@google.com (Gregg Bloom)']

PHONE_ORDER = [
    'work',
    'work_mobile',
    'work_pager',
    'work_fax',
    'mobile',
    'pager',
    'fax',
    'main',
    'company_main',
    'home',
    'home_fax',
    'assistant',
    'callback',
    'car',
    'isdn',
    'radio',
    'telex',
    'tty_tdd',
    'other',
    'other_fax',
]

import datetime
import logging
import sys

from getpass import getpass
from optparse import OptionParser

import gdata.apps.service as apps_service
import gdata.contacts
import gdata.contacts.service


def ParseInputs():
  parser = OptionParser()
  parser.add_option('-d', dest='domain',
                    help="""Domain""")
  parser.add_option('-u', dest='admin_user',
                    help="""Admin user""")
  parser.add_option('-p', dest='admin_pass_file',
                    help="""Admin password file""")
  parser.add_option('-l', dest='profiles_to_change',
                    help="""OPTIONAL:A comma-separated list of usernames
                            (without domain) to search.
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


def main():
  options = ParseInputs()

  # Set up logging
  log_filename = ('profile_phone_reorder_%s.log' %
                  (datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  if not options.apply:
    logging.info('RUNNING IN DRY RUN MODE, NO CHANGES WILL BE MADE')

  if options.admin_pass_file:
    password_file = open(options.admin_pass_file)
    password = password_file.readline().rstrip()
    password_file.close()
  else:
    password = getpass('Enter the password for user %s: '
                               % options.admin_user)

  con_conn = GetContactsConnection(options.admin_user,
                                   password,
                                   options.domain)
  prov_conn = GetProvConnection(options.admin_user,
                                password,
                                options.domain)

  # Define User List
  users = []
  if options.profiles_to_change:
    users = options.profiles_to_change.split(',')
  else:
    user_feed = prov_conn.RetrieveAllUsers()
    for user_entry in user_feed.entry:
      users.append(user_entry.login.user_name)

  for u in users:
    logging.info('User: %s:' % u)
    entry_uri = 'https://www.google.com'
    entry_uri += con_conn.GetFeedUri(kind='profiles',
                                    projection='full')
    entry_uri += '/' + u + '?v=3.0'
    try:
      entry = con_conn.GetProfile(entry_uri)
    except:
      logging.info('  Google+ error: Profile could not be loaded.')
      continue

    if not entry.phone_number:
      logging.info('  No phone numbers in profile.')
      continue

    if len(entry.phone_number) == 1:
      logging.info('  Only one phone entry. No need to re-order.')
      continue

    logging.info('  Original phone order:')
    order = {}
    for position in range(len(entry.phone_number)):
      phone_number = entry.phone_number[position]

      rel_type = phone_number.rel[33:]
      logging.info('    %s: %s' % (rel_type, phone_number.text))
      if rel_type not in order:
        order[rel_type] = [position]
      else:
        order[rel_type].append(position)

    new_order = []
    for rel_type in PHONE_ORDER:
      if rel_type in order:
        for position in order[rel_type]:
          new_order.append(entry.phone_number[position])
        del(order[rel_type])

    rel_types = order.keys()
    for rel_type in rel_types:
      for position in order[rel_type]:
        new_order.append(entry.phone_number[position])
      del(order[rel_type])

    logging.info('  New order:')
    for phone_number in new_order:
      rel_type = phone_number.rel[33:]
      logging.info('    %s: %s' % (rel_type, phone_number.text))

    if options.apply:
      entry.phone_number = new_order
      logging.info('  Updating Profile')
      con_conn.UpdateProfile(edit_uri=entry.GetEditLink().href,
                             updated_profile=entry)
    else:
      logging.info('  Not updating profile. Use -a to write.')

  print 'Log file: %s' % (log_filename)


if __name__ == '__main__':
  main()
