#!/usr/bin/python
#
# Copyright 2010 Google Inc. All Rights Reserved.

"""Loads groups and members from CSV files.

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
   THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR ITS DERIVATIVES.
   ###########################################################################

   Accepts two types of CSV files.  One or both can be present:
     For Groups:
       - Use the -g input parameter for the groups file
       - Must have column headers:
           "group_id","group_name","description","email_permission"
       - email_permission values must be one of ('Owner', 'Member',
                                                 'Domain', 'Anyone')
     For Members:
       - Use the -m input parameter for the members file
       - Must have column headers: "group_id","member_id"

   CSV files should be created with a comma as the field delimiter
   and double-quotes as the text delimiter.

   Operations performed (successes and failures) will be logged for later
   review.  Upon completion the log file name is printed.
"""

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import csv
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
  parser.add_option('-g', dest='groups_file',
                    help='The input file containing groups to create.')
  parser.add_option('-m', dest='members_file',
                    help="""The input file containing the members
                            to add to the groups.""")

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
  if options.groups_file is None and options.members_file is None:
    print 'Either -g (groups file) or -m (members file) is required'
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


def CSVReader(input_file):
  """Creates a CSV DictReader Object.

  The function opens a csv file and sets the first line of the file as
  headers.  A Dictreader object is then created with these headers.

  Args:
    input_file: [string] filename of CSV file to open.

  Returns:
    DictReader object
  """
  f = open(input_file, 'r')
  reader = csv.reader(f)
  headers = reader.next()
  reader = csv.DictReader(f, headers)
  return reader


def ValidateGroupsFile(input_file):
  """Checks groups file column headers and email_permissions possible values."""

  row_dict = CSVReader(input_file)

  headers = row_dict.fieldnames
  if headers[0] != 'group_id':
    print 'First column must contain header "group_id"'
    sys.exit(1)
  if headers[1] != 'group_name':
    print 'First column must contain header "group_name"'
    sys.exit(1)
  if headers[2] != 'description':
    print 'First column must contain header "description"'
    sys.exit(1)
  if headers[3] != 'email_permission':
    print 'First column must contain header "email_permission"'
    sys.exit(1)

  allowed_email_perms = ['Owner', 'Member', 'Domain', 'Anyone']
  rownum = 1
  for row in row_dict:
    if row['email_permission'] not in allowed_email_perms:
      print ('Row #%d contains an unsupported email_permission value [%s]'
             % (rownum, row['email_permission']))
      print 'Acceptable values are %s' % allowed_email_perms
      print 'Exiting to allow the data to be corrected'
      sys.exit(1)
    rownum += 1


def ValidateMembersFile(input_file):
  """Checks that the members file column headers are as expected."""

  row_dict = CSVReader(input_file)

  headers = row_dict.fieldnames
  if headers[0] != 'group_id':
    print 'First column must contain header "group_id" with group_id content'
    sys.exit(1)
  if headers[1] != 'member_id':
    print 'First column must contain header "member_id" with member_id content'
    sys.exit(1)


def ProcessGroups(options):
  """Uses the Groups Service to create groups according to input file."""

  ValidateGroupsFile(options.groups_file)

  row_dict = CSVReader(options.groups_file)

  success_count = 0
  failed_count = 0

  groups_connection = GroupsConnect(options)

  for row in row_dict:
    print 'Adding group %s' % row['group_id']
    logging.info('Adding group %s', row['group_id'])
    try:
      groups_connection.CreateGroup(row['group_id'],
                                    row['group_name'],
                                    row['description'],
                                    row['email_permission'])
      success_count += 1
    except Exception, e:
      logging.error('Creation failed for group %s with: %s',
                    row['group_id'],
                    str(e))
      failed_count += 1

  print 'Completed Group creates for %d groups' % (success_count + failed_count)
  print '  Failed     creates:%d' % failed_count
  print '  Successful creates:%d' % success_count


def ProcessMembers(options):
  """Uses the Groups Service to create members in existing groups."""

  ValidateMembersFile(options.members_file)

  row_dict = CSVReader(options.members_file)

  success_count = 0
  failed_count = 0

  groups_connection = GroupsConnect(options)

  for row in row_dict:
    print 'Adding member %s to group %s' % (row['member_id'], row['group_id'])
    logging.info('Adding member %s to group %s',
                 row['member_id'], row['group_id'])
    try:
      groups_connection.AddMemberToGroup(row['member_id'], row['group_id'])
      success_count += 1
    except Exception, e:
      logging.error('Creation failed for member %s to group %s with: %s',
                    row['member_id'], row['group_id'], str(e))
      failed_count += 1

  print ('Completed Member creates for %d members'
         % (success_count + failed_count))
  print '  Failed     creates:%d' % failed_count
  print '  Successful creates:%d' % success_count


def main():

  options = ParseInputs()

  # Set up logging
  log_filename = 'update_groups_%s.log' % GetTimeStamp()
  logging.basicConfig(filename=log_filename, level=logging.DEBUG)

  # If groups file given, create them first, then add members
  if options.groups_file:
    ProcessGroups(options)
  if options.members_file:
    ProcessMembers(options)

  print 'Log file is: %s' % log_filename


if __name__ == '__main__':
  main()
