#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Dumps file containing a line per group with a count of members therein.

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

   Produces an output file called groups_counts.csv containing two columns.
     - Group ID - the group email address
     - Members count - simply a count of the number of members

   Produces a line for each group regardless of whether group has zero members.

   NOTE: The script must pull a member list for every group, so it may take some time
         to pull all groups.

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


def main():

  options = ParseInputs()

  # Create dict to store members per group
  grp = {}

  groups_connection = GroupsConnect(options)
  all_groups = groups_connection.RetrieveAllGroups()

  for group in all_groups:

    print "Pulling info for group [%s]" % group['groupId']

    grp[group['groupId']] = []

    member_feed = groups_connection.RetrieveAllMembers(group['groupId'])
    for member in member_feed:

      grp[group['groupId']].append(member['memberId'])

  out_file = csv.writer(open('groups_counts.csv', 'wb'), delimiter=',',
                              quotechar='"', quoting=csv.QUOTE_MINIMAL)
  out_file.writerow(['group_id', 'member_count'])

  for k, v in grp.items():
    out_file.writerow([k, len(v)])
  
if __name__ == '__main__':
  main()
