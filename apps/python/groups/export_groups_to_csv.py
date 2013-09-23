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

import csv
import datetime
from optparse import OptionParser
import re
import sys
import gdata.apps.groups.service as groups_service


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  parser = OptionParser()
  parser.add_option('-d', dest='domain',
                    help='The domain name in which to add groups.')
  parser.add_option('-u', dest='admin_user',
                    help='The admin user to use for authentication.')
  parser.add_option('-p', dest='admin_pass',
                    help="The admin user's password")
  parser.add_option('-g', dest='groups_output_filename', default='groups.csv',
                    help='The output file to write the group data to.')
  parser.add_option('-m', dest='members_output_filename', default='members.csv',
                    help="""The output file to write the members data to.""")
  parser.add_option('-n', dest='new_domain_name',
                    help="""If present, will replace the domain (-d) with
                            this new domain name in the email addresses for the
                            groups as well as members.""")

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
    print '-p (admin password) is required'
    sys.exit(1)

  return options


def GroupsConnect(options):
  service = groups_service.GroupsService(email=options.admin_user,
                                         domain=options.domain,
                                         password=options.admin_pass)
  service.ProgrammaticLogin()
  return service


def InitializeOutputFiles(group_filename, member_filename):
  """Creates files with headers for groups and member data."""

  # Create groups output file
  groups_file = csv.DictWriter(open(group_filename, 'w'),
                               fieldnames=['group_id',
                                           'group_name',
                                           'description',
                                           'email_permission'],
                               delimiter=',')
  groups_file.writerow({'group_id': 'group_id',
                        'group_name': 'group_name',
                        'description': 'description',
                        'email_permission': 'email_permission'})

  # Create members output file
  members_file = csv.DictWriter(open(member_filename, 'w'),
                                fieldnames=['group_id',
                                            'member_id'],
                                delimiter=',')
  members_file.writerow({'group_id': 'group_id',
                         'member_id': 'member_id'})

  return (groups_file, members_file)


def DomainSub(email_address, old_domain, new_domain):
  if new_domain:
    p = re.compile('@' + old_domain + '$', re.IGNORECASE)
    return re.sub(p, '@' + new_domain, email_address)
  else:
    return email_address


def main():

  options = ParseInputs()

  (group_f, member_f) = InitializeOutputFiles(options.groups_output_filename,
                                              options.members_output_filename)

  groups_connection = GroupsConnect(options)
  all_groups = groups_connection.RetrieveAllGroups()

  for group in all_groups:
    group_f.writerow({'group_id': DomainSub(group['groupId'],
                                            options.domain,
                                            options.new_domain_name),
                      'group_name': group['groupName'],
                      'description': group['description'],
                      'email_permission': group['emailPermission']})

    member_feed = groups_connection.RetrieveAllMembers(group['groupId'])
    for member in member_feed:
      member_f.writerow({'group_id': DomainSub(group['groupId'],
                                               options.domain,
                                               options.new_domain_name),
                         'member_id': DomainSub(member['memberId'],
                                                options.domain,
                                                options.new_domain_name)})


if __name__ == '__main__':
  main()
