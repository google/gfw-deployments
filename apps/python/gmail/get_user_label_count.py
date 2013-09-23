#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Prints number of labels for each user in a domain.

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

Usage: get_user_label_count.py [options]

Options:
  -h, --help     show this help message and exit
  -d DOMAIN      The domain name to log into.
  -u ADMIN_USER  The admin user to use for authentication.
  -p ADMIN_PASS  The admin user's password
"""


__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

from optparse import OptionParser
import sys
import gdata.apps.emailsettings.client
import gdata.apps.service


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  parser = OptionParser()
  parser.add_option('-d', dest='domain',
                    help='The domain name to log into.')
  parser.add_option('-u', dest='admin_user',
                    help='The admin user to use for authentication.')
  parser.add_option('-p', dest='admin_pass',
                    help="The admin user's password")

  (options, args) = parser.parse_args()
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))

  invalid_args = False
  if options.domain is None:
    print '-d (domain) is required'
    invalid_args = True
  if options.admin_user is None:
    print '-u (admin user) is required'
    invalid_args = True
  if options.admin_pass is None:
    print '-p (admin password) is required'
    invalid_args = True

  if invalid_args:
    sys.exit(4)

  return options


def SettingsConnect(options):
  client = gdata.apps.emailsettings.client.EmailSettingsClient(
      domain=options.domain)
  client.ClientLogin(email=options.admin_user,
                     password=options.admin_pass,
                     source='get-label-count-python')
  return client

def ProvisioningConnection(options):
  client = gdata.apps.service.AppsService(email=options.admin_user,
                                          domain=options.domain,
                                          password=options.admin_pass)
  client.ProgrammaticLogin()
  return client

def GetProvisionedUsers(connection):
  users = []
  user_feed = connection.RetrieveAllUsers()
  for user_entry in user_feed.entry:
    users.append(user_entry.login.user_name.lower())
  return users

def main():

  options = ParseInputs()

  settings_conn = SettingsConnect(options)
  prov_conn = ProvisioningConnection(options)

  all_users = GetProvisionedUsers(prov_conn)

  label_profiles = {}

  print "Retrieving label counts per user"

  for user in all_users:
    labels = settings_conn.RetrieveLabels(username=user)
    counter = 0
    for label in labels.entry:
      counter += 1

    label_profiles[user] = counter

  print "Done retrieving label counts per user"

  sorted_user_label_list = sorted(label_profiles.iteritems(), key=lambda (k,v):(v,k), reverse=False)
  for (user,cnt) in sorted_user_label_list:
    print user,cnt

if __name__ == '__main__':
  main()
