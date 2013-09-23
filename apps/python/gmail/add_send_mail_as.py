#!/usr/bin/python
#
# Copyright 2010 Google Inc. All Rights Reserved.

"""Adds a send mail as to a users Gmail account.

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

Usage: add_send_mail_as.py [options]

Options:
  -h, --help            show this help message and exit
  -d DOMAIN             The domain name to log into.
  -u ADMIN_USER         The admin user to use for authentication.
  -p ADMIN_PASS         The admin user's password
  --mailuser=MAILUSER   Username to add Send Mail As setting to.
                        (just username without domain)
  -n NAME               Name to be given to email address.
  --email_address=EMAIL_ADDRESS
                        Email address to set as a Send Mail As.
  --make_default        Makes this email address the default Send Mail As.
                        DEFAULT: is False

"""


__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

from optparse import OptionParser
import sys
import gdata.apps.emailsettings.client


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""

  parser = OptionParser()
  parser.add_option('-d', dest='domain',
                    help='The domain name to log into.')
  parser.add_option('-u', dest='admin_user',
                    help='The admin user to use for authentication.')
  parser.add_option('-p', dest='admin_pass',
                    help="The admin user's password")
  parser.add_option('--mailuser', dest='mailuser',
                    help="""Username to add Send Mail As setting to.
                            (just username without domain)""")
  parser.add_option('-n', dest='name',
                    help="""Name to be given to email address.""")
  parser.add_option('--email_address', dest='email_address',
                    help="""Email address to set as a Send Mail As.""")
  parser.add_option('--make_default', dest='make_default', action='store_true',
                    default=False,
                    help="""Makes this email address the default Send Mail As.
                            DEFAULT: is False""")

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
  if options.mailuser is None:
    print '--mailuser (mailuser) is required'
    invalid_args = True
  if options.name is None:
    print '-n (name) is required'
    invalid_args = True
  if options.email_address is None:
    print '--email_address (email_address) is required'
    invalid_args = True

  if invalid_args:
    sys.exit(4)

  return options


def SettingsConnect(options):
  client = gdata.apps.emailsettings.client.EmailSettingsClient(
      domain=options.domain)
  client.ClientLogin(email=options.admin_user,
                     password=options.admin_pass,
                     source='add-send-mail-as-python')
  return client


def main():

  options = ParseInputs()

  settings_conn = SettingsConnect(options)

  try:
    settings_conn.CreateSendAs(username=options.mailuser,
                               name=options.name,
                               address=options.email_address,
                               make_default=options.make_default)
    print ('Send mail as set to [%s] with name [%s] for user [%s] successful' %
           (options.email_address, options.name, options.mailuser))
  except Exception, e:
    print ('Setting Send mail as to [%s] user [%s] failed with [%s].' %
           (options.email_address, options.mailuser, e))


if __name__ == '__main__':
  main()
