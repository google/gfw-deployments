#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Dumps user data to file that can be used to import into Google Apps.

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

NOTE: The password in the output file is *NOT* the actual password.
      Rather this is intended to allow you to specify a new password
      for uploading the CSV of these users to another Apps account.

Usage: export_users_to_csv.py [options]

Options:
  -h, --help            show this help message and exit
  -d DOMAIN             The domain name in which to add groups.
  -u ADMIN_USER         The admin user to use for authentication.
  -p ADMIN_PASS         The admin user's password
  -o USERS_OUTPUT_FILENAME
                        The output file to write the user data to.
                        Defaults to users.csv
  -n NEW_DOMAIN_NAME    If present, will replace the domain (-d) with
                        this new domain name in the email addresses for
                        the users.

"""

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import csv
from optparse import OptionParser
import random
import re
import string
import sys
import gdata.apps.service as apps_service


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  parser = OptionParser()
  parser.add_option('-d', dest='domain',
                    help='The domain name in which to add groups.')
  parser.add_option('-u', dest='admin_user',
                    help='The admin user to use for authentication.')
  parser.add_option('-p', dest='admin_pass',
                    help="The admin user's password")
  parser.add_option('-o', dest='users_output_filename', default='users.csv',
                    help='The output file to write the user data to.')
  parser.add_option('-n', dest='new_domain_name',
                    help="""If present, will replace the domain (-d) with
                            this new domain name in the email addresses for
                            the users.""")

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

  if options.new_domain_name is None:
    options.new_domain_name = options.domain
  else:
    pass

  return options


def GetConnection(options):
  service = apps_service.AppsService(email=options.admin_user,
                                     domain=options.domain,
                                     password=options.admin_pass)
  service.ProgrammaticLogin()
  return service


def InitializeOutputFile(user_filename):
  """Creates file with headers for user data."""

  # Create groups output file
  users_file = csv.DictWriter(open(user_filename, 'w'),
                              fieldnames=['email address',
                                          'first name',
                                          'last name',
                                          'password'],
                              delimiter=',')
  users_file.writerow({'email address': 'email address',
                       'first name': 'first name',
                       'last name': 'last name',
                       'password': 'password'})

  return users_file


def GeneratePassword():
  return ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(8))


def main():

  options = ParseInputs()

  user_f = InitializeOutputFile(options.users_output_filename)

  connection = GetConnection(options)
  user_feed = connection.RetrieveAllUsers()

  for user_entry in user_feed.entry:
    user_f.writerow({'email address': '%s@%s' % (user_entry.login.user_name,
                                                 options.new_domain_name),
                     'first name': user_entry.name.given_name,
                     'last name': user_entry.name.family_name,
                     'password': '%s' % (GeneratePassword())})


if __name__ == '__main__':
  main()
