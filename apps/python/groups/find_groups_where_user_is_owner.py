#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""For a specific user, prints groups for which they are owner.

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

Summary: This script allows an administrator to search for groups
         for which a specific user is an owner of that group.

Usage: find_groups_where_user_is_owner.py [options]

Options:
  -h, --help     show this help message and exit
  -d DOMAIN      The domain name in which to add groups.
  -u ADMIN_USER  The admin user to use for authentication.
  -p ADMIN_PASS  The admin user's password
  -m MEMBER      The member of the group for which we want to
                 find all groups where they are owner.

"""

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import datetime
import logging
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
  parser.add_option('-m', dest='member',
                    help="""The member of the group for which we want to
                            find all groups where they are owner.""")

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
  if options.member is None:
    print '-m (member) is required'
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
  log_filename = 'find_groups_where_user_is_owner_%s.log' % GetTimeStamp()
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  conn = GroupsConnect(options)

  groups = conn.RetrieveAllGroups()

  for group in groups:
    try:
      logging.info('Inspecting Group: [%s]', group['groupId'])
      members = conn.RetrieveAllMembers(group['groupId'])
      for member in members:
        if (member['memberId'] == options.member and
            conn.IsOwner(member['memberId'], group['groupId'])):
          logging.info('[%s] is owner of group [%s]', member['memberId'],
                       group['groupId'])
    except Exception, e:
      logging.error('Failure processing group [%s] with [%s]',
                    group['groupId'], str(e))

  print 'Log file is: %s' % log_filename


if __name__ == '__main__':
  main()
