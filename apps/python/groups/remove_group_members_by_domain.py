#!/usr/bin/python
#
# Copyright 2010 Google Inc. All Rights Reserved.

"""
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

Summary: This script allows an administrator to search a specific group
         or all primary and secondary domain groups within a
         Apps account for members with a specific domain name
         and deletes them if requested.

Usage: remove_group_members_by_domain.py [options]

Options:
  -h, --help         show this help message and exit
  -d DOMAIN          The Apps primary domain name.
  -u ADMIN_USER      The admin user to use for authentication.
  -p ADMIN_PASS      The admin user's password
  -g GROUP_ADDRESS   OPTIONAL:If interested in searching a single group, you can
                     pass in a single group email address.
  -r REMOVAL_DOMAIN  Group members with this domain will be removed
                     from groups.
  -a                 Applies the deletions.  If this flag is not present,
                     script will run in dry run mode, making no changes.

Ex.
  # For Dry Run (no modifications made)
  remove_group_members_by_domain.py -d mdauphinee.info
                                    -u administrator@mdauphinee.info
                                    -p mypass
                                    -r hotmail.com

  # To apply changes
  # Deletes all members with hotmail.com addresses
  remove_group_members_by_domain.py -d mdauphinee.info
                                    -u administrator@mdauphinee.info
                                    -p mypass
                                    -r hotmail.com
                                    -a

"""


__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import datetime
import logging
import re
from optparse import OptionParser
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
  parser.add_option('-g', dest='single_group',
                    help="""OPTIONAL:If interested in searching a single group,
                            you can pass in a single group email address.""")
  parser.add_option('-r', dest='removal_domain',
                    help="""Group members with this domain will be removed
                            from groups.""")
  parser.add_option('-a', dest='apply', action="store_true", default=False,
                    help="""Applies the deletions.  If this flag is not present,
                            script will run in dry run mode, making no changes.""")

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
  if options.removal_domain is None:
    print '-r (removal domain) is required'
    sys.exit(1)

  return options


def GetTimeStamp():
  now = datetime.datetime.now()
  return now.strftime('%Y%m%d%H%M%S')


def GroupsConnect(options):
  service = groups_service.GroupsService(email=options.admin_user,
                                         domain=options.domain,
                                         password=options.admin_pass)
  service.ProgrammaticLogin()
  return service


def main():

  options = ParseInputs()

  # Set up logging
  log_filename = 'remove_group_members_by_domain_%s.log' % GetTimeStamp()
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  if not options.apply:
    logging.info("RUNNING IN DRY RUN MODE, NO CHANGES WILL BE MADE")

  conn = GroupsConnect(options)

  groups = []

  if options.single_group:
    d = {}
    d['groupId'] = options.single_group
    groups.append(d)
  else:
    groups = conn.RetrieveAllGroups()

  for group in groups:
    try:
      logging.info("Inspecting Group: [%s]", group['groupId'])
      members = conn.RetrieveAllMembers(group['groupId'])
      for member in members:
        p = re.compile('@' + options.removal_domain + '$', re.IGNORECASE)
        if re.search(p, member['memberId']):
          # Delete the user
          if options.apply:
            logging.info("Removing user [%s] from group [%s]",
                         member['memberId'], group['groupId'])
            conn.RemoveMemberFromGroup(member['memberId'], group['groupId'])
          else:
            logging.info("Would have deleted user [%s] from group [%s]",
                         member['memberId'], group['groupId'])
    except Exception, e:
      logging.error("Failure processing group [%s] with [%s]",
                    group['groupId'], str(e))

  print 'Log file is: %s' % log_filename


if __name__ == '__main__':
  main()
