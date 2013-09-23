#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""For a list of users, changes the password and emails the new password.

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

Usage: password_change.py [options]

Options:
  -h, --help            show this help message and exit
  -u ADMIN_USER         The admin user. Use full email address.
                        Operator will be prompted for password.
  -d DOMAIN             The Google Apps domain name.
  -f SENDER_ADDRESS     The address to include in the from address.
  --generate_password   OPTIONAL: If specified, password column in input
                        file will be ignored and password will be generated
                        for each user.
  -l GENERATED_PASSWORD_LENGTH
                        OPTIONAL: The generated password length desired.
                        Defaults to 8 characters.
  -i INPUT_FILE         CSV file with list of users.
                        File must have a header with the fields:
                        username, password

NOTE: This script only works for users on the primary domain
      of the Google Apps account.

NOTE: This script currently uses localhost as the sending MTA.

"""

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'


import csv
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass
import logging
from optparse import OptionParser
import random
import re
import smtplib
import string
import sys
import gdata.apps.service


def ParseInputs():
  """Interprets command line parameters and checks for required parameters.

  Returns:
    The options object of parsed command line options.
  """

  parser = OptionParser()
  parser.add_option('-u', dest='admin_user',
                    help="""The admin user. Use full email address.
                            Operator will be prompted for password.""")
  parser.add_option('-d', dest='domain',
                    help='The Google Apps domain name.')
  parser.add_option('-f', dest='sender_address',
                    help='The address to include in the from address.')
  parser.add_option('--generate_password', action='store_true', default=False,
                    help="""OPTIONAL: If specified, password column in input
                            file will be ignored and password will be generated
                            for each user.""")
  parser.add_option('-l', dest='generated_password_length',
                    default=8, type='int',
                    help="""OPTIONAL: The generated password length desired.
                            Defaults to 8 characters.""")
  parser.add_option('-i', dest='input_file',
                    help="""CSV file with list of users.
                            File must have a header with the fields:
                               username, password""")

  (options, args) = parser.parse_args()
  if args:
    parser.print_help()
    parser.exit(msg='\nUnexpected arguments: %s\n' % ' '.join(args))

  invalid_arguments = False
  if options.admin_user is None:
    print '-u (admin_user) is required'
    invalid_arguments = True
  if options.domain is None:
    print '-d (domain) is required'
    invalid_arguments = True
  if options.sender_address is None:
    print '-f (sender_address) is required'
    invalid_arguments = True
  if options.input_file is None:
    print '-i (input_file) is required'
    invalid_arguments = True

  # Verify that password length is > 8 chars
  # which is required by Provisioning API
  if options.generated_password_length < 8:
    print 'Passwords must be at least 8 characters'
    invalid_arguments = True

  if invalid_arguments:
    sys.exit(1)

  return options


def GeneratePassword(password_length):
  """Function to generate passwords.

  Generates a random password of the length specified.  The new password will
  be a combination of ASCII lowercase letters and digits.  Does not enforce
  the presence of a digit.  Only enforces length.

  Args:
    password_length: Integer value specifying desired password length.

  Returns:
    A new password string.
  """

  return (''.join(random.choice(string.ascii_lowercase + string.digits)
                  for x in range(password_length)))


def GetTimeStamp():
  """Generates a string representing the current time for the log file name.

  Returns:
    A formatted string representing the current date and time.
  """

  now = datetime.datetime.now()
  return now.strftime('%Y%m%d%H%M%S')


def ExtractUserName(email_address):
  """Extracts the username string before the at sign in an email address.

  Isolates the username portion of an email address.
  (e.g. username@domain.com)

  Args:
    email_address: A full email address to parse.

  Returns:
    A string representing the portion of the email address before the at sign.
  """

  regex_obj = re.compile('(.+)@(.+)', re.IGNORECASE)
  regex_match_obj = regex_obj.match(email_address)
  return regex_match_obj.group(1)


def GetProvisioningConnection(admin_user, admin_pass, domain):
  """Gets a Provisioning API connection.

  Args:
    admin_user: The email address of the admin user.
    admin_pass: The password of the admin user.
    domain: The Google Apps domain to log into.

  Returns:
    A Provisioning API ClientLogin connection.
  """

  prov_api_connection = gdata.apps.service.AppsService(email=admin_user,
                                                       domain=domain,
                                                       password=admin_pass)
  prov_api_connection.ProgrammaticLogin()
  return prov_api_connection


def ChangePassword(api_connection, email_address, new_pass):
  """Changes the password for the given user.

  Changes the password for the user and specifies that the user
  must change it on lext login.

  Args:
    api_connection: The provisioning API connection handle.
    email_address: The full email address of the user needing a password change.
    new_pass: String with the password to be given to this user.
  """

  username = ExtractUserName(email_address)

  logging.info('Changing password for user [%s]', email_address)
  try:
    user_entry = api_connection.RetrieveUser(username)
    user_entry.login.password = new_pass
    api_connection.UpdateUser(username, user_entry)
  except Exception, e:
    logging.error('Error thrown when changing pass for user [%s] error [%s] ',
                  email_address, e)
    raise


def MailUser(user, passwd, sender):
  """Mails the password to the user.

  Sends the password to the user's email address.  This implementation
  builds a HTML message with an alternative plain text version.  This
  may be more than is necessary but allows an operator to customize the
  sent message, if necessary.

  Args:
    user: The email address of the user to be sent the new password.
    passwd: The new password that was given to the user.
    sender: The email address to be added as the From address when sent.
  """

  try:
    logging.info('Mailing password to user [%s]', user)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Your Google Apps Password Has Been Changed'
    msg['From'] = sender
    msg['To'] = user

    text = 'Your new password is %s' % passwd
    html = """\
    <html>
      <head></head>
      <body>
        <p><font face="courier">Your new password is %s</font></p>
      </body>
    </html>""" % passwd

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    smtp_client = smtplib.SMTP('localhost')
    smtp_client.sendmail(sender, user, msg.as_string())
    smtp_client.quit()
  except Exception, e:
    logging.error('Error thrown when mailing password to user [%s] error [%s] ',
                  user, e)
    raise


def ValidateHeaders(options):
  """Checks headers of input file.

  Validates the header of the input file are as required.  The input file
  must by in CSV format with a header added.  The first field in the header
  must be "username".  The second field should be "password", but is only
  required if --generate_password is not specified at the command line.

  Args:
    options: The command line options object.
  """

  input_file = open(options.input_file, 'r')
  reader = csv.reader(input_file)
  headers = reader.next()
  reader = csv.DictReader(input_file, headers)

  # Validate the headers
  invalid_file = False
  if headers[0] != 'username':
    invalid_file = True
    logging.critical('Invalid input file header:First field must be "username"')
  if not options.generate_password:
    if len(headers) > 1 and headers[1] != 'password':
      logging.critical('If --generate_password is not present, second column'
                       'header must be "password"')
      invalid_file = True
    if len(headers) == 1:
      logging.critical('If --generate_password is not present, second column'
                       'must be present and must be "password"')
      invalid_file = True

  if invalid_file:
    sys.exit(1)


def PrintSummary(fail_count, success_count, log_filename):
  """Prints summary of processing numbers."""

  logging.info('Password changes complete.')
  logging.info('########### Summary ###########')
  logging.info('Total users in file: %d',
               (success_count + fail_count))
  logging.info('Successful updates: %d', success_count)
  logging.info('Failed updates: %d', fail_count)
  if fail_count > 0:
    print """WARNING: Failures in processing some users.
             Review log file for users not completed."""
  print 'Log file is: %s' % log_filename


def main():

  options = ParseInputs()

  # Prompt user for administrator user password
  admin_pass = (getpass.getpass(prompt='Enter password for user %s: ' %
                                options.admin_user))

  # Set up logging
  log_filename = 'password_change_%s.log' % GetTimeStamp()
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                      filename=log_filename,
                      level=logging.DEBUG)
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  logging.getLogger('').addHandler(console)

  ValidateHeaders(options)

  # Open input file for reading
  file_handle = open(options.input_file, 'r')
  reader = csv.reader(file_handle)
  headers = reader.next()
  reader = csv.DictReader(file_handle, headers)

  api_connection = GetProvisioningConnection(options.admin_user, admin_pass,
                                             options.domain)

  # Initialize variables to track processing numbers
  processing_successes = 0
  processing_failures = 0

  for line in reader:
    if options.generate_password:
      new_pass = GeneratePassword(options.generated_password_length)
    else:
      new_pass = line['password']

    try:
      ChangePassword(api_connection, line['username'], new_pass)
      MailUser(line['username'], new_pass, options.sender_address)
      processing_successes += 1
    except Exception, e:
      logging.critical('Error processing user [%s]. Error: %s',
                       line['username'], e)
      processing_failures += 1

  PrintSummary(processing_failures, processing_successes, log_filename)


if __name__ == '__main__':
  main()
