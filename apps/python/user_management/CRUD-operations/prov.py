#!/usr/bin/python2.5

"""prov: performs CRUD operations for a Google Apps domain."""

__author__ = 'jeff.stanway@gmail.com'


import csv
import getpass
import optparse
import sys
import gdata.apps.service

# GData error codes for information in case an exception is thrown
ERROR_DICT = {
    '1000': 'UnknownError', '1100': 'UserDeletedRecently',
    '1101': 'UserSuspended', '1200': 'DomainUserLimitExceeded',
    '1201': 'DomainAliasLimitExceeded', '1202': 'DomainSuspended',
    '1203': 'DomainFeatureUnavailable', '1300': 'EntityExists',
    '1301': 'EntityDoesNotExist', '1302': 'EntityNameIsReserved',
    '1303': 'EntityNameNotValid', '1400': 'InvalidGivenName',
    '1401': 'InvalidFamilyName', '1402': 'InvalidPassword',
    '1403': 'InvalidUsername', '1404': 'InvalidHashFunctionName',
    '1405': 'InvalidHashDigestLength', '1406': 'InvalidEmailAddress',
    '1407': 'InvalidQueryParameterValue', '1500': 'TooManyRecipientsOnList'}


class ProvTools(object):
  """ProvTools object defines functions to perform CRUD operations."""

  def __init__ (self, email, domain, password):
    """Constructor for the ProvTools object.

    Takes an email and password for an administrator of a given Google Apps
    domain.  Creates a new AppsService object and invokes ProgrammaticLogin()
    to authenticate administraor to the domain.

    Args:
      email: [string] The e-mail address of the adminsitrator account
      domain: [string] The Google Apps domain to authenticate to
      password: [string] The password corresponding to the account specified by
        the email parameter.
    """

    self.gd_client = gdata.apps.service.AppsService()
    self.gd_client.email = email
    self.gd_client.domain = domain
    self.gd_client.password = password
    self.gd_client.ProgrammaticLogin()

  def CreateUser(self, row):
    """Creates a new user based on variables from a row in a csv file.

    The function invokes the AppsService.CreateUser() method to create a
    user.  If it is successful, it will record 'success', If
    there are any errors it will catch and record the error.

    The CreateUser() method does not support creating a user as an admin or
    setting login.change.password to true.  In these cases, after creating the
    user we then need to retrieve that user, set the login.admin and
    login.change.password attributes to True, and then update the user.

    Args:
      row: a dictionary object that contains a row from a csv file.  Keys in
        the dictionary are the headers in the csv file.

    Raises:
      gdata.apps.service.AppsForYourDomainException if an exception is thrown
    """
    if 'quota_limit' in row.keys() and row['quota_limit']:
      quota = row['quota_limit']
    else:
      quota = 25000
    if 'pw_hash_function' in row.keys() and row['pw_hash_function']:
      pw_hash_function = row['pw_hash_function']
    else:
      pw_hash_function = None
    if 'suspended' in row.keys() and row['suspended']:
      suspended_flag = row['suspended']
    else:
      suspended_flag = 'FALSE'
    try:
      self.gd_client.CreateUser(
          row['user_name'], row['family_name'], row['given_name'],
          row['password'], suspended=suspended_flag,
          password_hash_function=pw_hash_function, quota_limit=quota)
      row['status'] = 'success'
    except gdata.apps.service.AppsForYourDomainException, e:
      row['status'] = 'fail gdata error code:%s %s'% (
          e.error_code, ERROR_DICT[str(e.error_code)])
    except KeyError:
      print ('user_name, given_name, family_name, password are required\n'
             'headers when action is create')
      sys.exit()
    # if user is admin, IP_whistelisted, or change password required, 
    # we need to do the following    
    if ('admin' not in row.keys() and 'change_pw' not in row.keys()
        and 'ip_whitelisted' not in row.keys()):
      return
    try:
      user_feed = self.gd_client.RetrieveUser(row['user_name'])
      if 'admin' in row.keys() and row['admin']:
        user_feed.login.admin = row['admin']
      else:
        user_feed.login.admin = 'FALSE'
      if 'change_pw' in row.keys() and row['change_pw']:
        user_feed.login.change_password = row['change_pw']
      else:
        user_feed.login.change_password = 'FALSE'
      if 'ip_whitelisted' in row.keys() and row['ip_whitelisted']:
        user_feed.login.ip_whitelisted = row['ip_whitelisted']
      else:
        user_feed.login.ip_whitelisted = 'FALSE'
      self.gd_client.UpdateUser(row['user_name'], user_feed)
    except gdata.apps.service.AppsForYourDomainException, e:
      row['status'] = (
          'fail: gdata error code:%s %s'%
          (e.error_code, ERROR_DICT[str(e.error_code)]))

  def UpdateUser(self, row):
    """Updates an existing user based on variables from a row in a csv file.

    The function firstly invoke the AppsService.RetrieveUser() method to
    retrieve a user feed.  It then compares the values in the csv row
    with the corresponding attribute values in the user feed.
    If the values are different, the exisiting value in the user feed row
    is updated with the value from the CSV row.  The AppsService.UpdateUser()
    method is then invoked to update the user row with the new attributes.

    If the csv row specifies a new user name for a user, we need to update the
    login.user_name attibute for the user_row object and then invoke the
    AppsService.UpdateUser() method with the old username.

    Args:
      row: a dictionary object that contains a row from a csv file.  Keys in
        the dictionary are the headers in the csv file.

    Raises:
      gdata.apps.service.AppsForYourDomainException if an exception is thrown
    """
    try:
      user_feed = self.gd_client.RetrieveUser(row['user_name'])
    except gdata.apps.service.AppsForYourDomainException, e:
      row['status'] = ('fail gdata error code: %s %s' %
                       (e.error_code, ERROR_DICT[str(e.error_code)]))
      # if we cant even retrieve the user feed, no point in carrying on
      return
    except KeyError:
      print 'user_name is a required header when action is create'
      sys.exit()

    if 'given_name' in row.keys() and row['given_name']:
      user_feed.name.given_name = row['given_name']
    if 'family_name' in row.keys() and row['family_name']:
      user_feed.name.family_name = row['family_name']
    if 'password' in row.keys() and row['password']:
      user_feed.login.password = row['password']
    if 'ip_whitelisted' in row.keys() and row['ip_whitelisted']:
      user_feed.login.ip_whitelisted = row['ip_whitelisted']
    if 'suspended' in row.keys() and row['suspended']:
      user_feed.login.suspended = row['suspended']
    if 'quota_limit' in row.keys() and row['quota_limit']:
      user_feed.quota.limit = row['quota_limit']
    if 'new_user_name' in row.keys() and row['new_user_name']:
      user_feed.login.user_name = row['new_user_name']
    if 'change_pw' in row.keys() and row['change_pw']:
      user_feed.login.change_password = row['change_pw']
    if 'pw_hash_function' in row.keys() and row['pw_hash_function']:
      user_feed.login.hash_function_name = row['pw_hash_function']
    if 'admin' in row.keys() and row['admin']:
      user_feed.login.admin = row['admin']
    # update the user_feed object with the new attibutes
    try:
      self.gd_client.UpdateUser(row['user_name'], user_feed)
      row['status'] = 'success'
    except gdata.apps.service.AppsForYourDomainException, e:
      row['status'] = ('fail: gdata error code: %s %s' %
                       (e.error_code, ERROR_DICT[str(e.error_code)]))

  def DeleteUser(self, row):
    """Deletes an existing user based on variables from a row in a csv file.

    The function invokes the AppsService.DeleteUser() method to delete a
    user.  If it is successful, it will record 'success', If
    there are any errors it will catch and record the error.

    Args:
      row: a dictionary object that contains a row from a csv file.  Keys in
        the dictionary are the headers in the csv file.

    Raises:
      gdata.apps.service.AppsForYourDomainException if an exception is thrown
    """
    try:
      self.gd_client.DeleteUser(row['user_name'])
      row['status'] = 'success'
    except gdata.apps.service.AppsForYourDomainException, e:
      row['status'] = (
          'fail gdata error code: %s %s' %
          (e.error_code, ERROR_DICT[str(e.error_code)]))
    except KeyError:
      print 'error - user_name is a required header'
      sys.exit()

  def CSVReader(self, input_file):
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

  def OutputWriter(self, report, output_file, output_field_names):
    """Creates a DictWriter object to write output to a CSV file.

    Fieldnames for the csv DictWriter object are different depending if
    the script is run in retrieve or process mode.

    Args:
      report: List object with all output lines to write to CSV.
        mode script is run (retrieve all users or process).
      output_file: [string] filename of CSV file to write to.
      output_field_names: List object with fieldnames for output CSV
    """
    csv_file = open(output_file, 'w')
    fieldnames = output_field_names
    writer = csv.DictWriter(csv_file, fieldnames)
    headers = {}
    for fieldname in fieldnames:
      headers[fieldname] = fieldname
    writer.writerow(headers)
    for row in report:
      writer.writerow(row)

  def GetAllUserInfo(self, output_file, verbose):
    """Retrieves all user info from domain.

    This function calls AppsService.RetrieveAllUsers() to retrive a user feed
    object containing all users in a given domain.  We enumerate over the
    user feed object and write a user's attibutes out into a Dictionary object,
    before adding the dictionary to a list and doing the same for the next user
    in the feed.

    Args:
     output_file: [string] Output filename for data to be written.
     verbose: [boolean] if true, print output to screen as well.
    """
    user_feed = self.gd_client.RetrieveAllUsers()
    report = []
    output_field_names = (
        'user_name', 'given_name', 'family_name', 'ip_whitelisted', 'suspended',
        'quota_limit', 'change_pw', 'admin', 'agreed_to_terms')

    for _, entry in enumerate(user_feed.entry):
      row = {
          'user_name': entry.login.user_name,
          'given_name': entry.name.given_name,
          'family_name': entry.name.family_name,
          'ip_whitelisted': entry.login.ip_whitelisted,
          'suspended': entry.login.suspended,
          'quota_limit': entry.quota.limit,
          'change_pw': entry.login.change_password,
          'admin': entry.login.admin,
          'agreed_to_terms': entry.login.agreed_to_terms}
      report.append(row)
      if verbose is True:
        print row
    self.OutputWriter(report, output_file, output_field_names)

  def ProcessCSV(self, input_file, verbose, output_file):
    """Uses data in CSV file to decide which CRUD function to call.

    This function takes each row from a CSV file and depending on the
    value in the 'action' column calls functions to create, update, or delete
    user accounts.

    Args:
      input_file: [string] filename of CSV file to open.
      verbose: [boolean] if true, print output to screen as well.
      output_file: [string] Output filename for data to be written.
    """
    row_dict = self.CSVReader(input_file)
    report = []
    output_field_names = row_dict.fieldnames
    output_field_names.append('status')

    for row in row_dict:
      if 'action' in row.keys():
        if row['action'] == 'create':
          self.CreateUser(row)
        elif row['action'] == 'update':
          self.UpdateUser(row)
        elif row['action'] == 'delete':
          self.DeleteUser(row)
        else:
          row['status'] = ('Error: action must be create, update, or delete for'
                           ' username %s' % (row['user_name']))
      else:
        print 'error - action is a required header in the input CSV file'
        sys.exit()

      # delete password attribute so we dont output that to screen or CSV
      if 'password' in row.keys():
        del row['password']
      report.append(row)
      if verbose is True:
        output = []
        list_tup = ()
        for k, v in row.items():
          if v:
            list_tup = (k, v)
            output.append(list_tup)
        print output
      self.OutputWriter(report, output_file, output_field_names)


def main():
  """Sets up parser to parse command line input and calls ProvTools().

  Main function sets up a command line parser and then calls ProvTools class
  to create a new AppsService object.

  Rasies:
    gdata.apps.service.AppsForYourDomainException if an exception is thrown.
  """
  help_text = (
      'Examples:\n\n'
      ' Log into Google Apps domain bla.com as admin user bla-admin\n'
      ' Retrieve a list all users in the domain, then save to a file\n'
      ' called bla-users.csv and output to screen\n\n'
      '       ./prov.py -u admin -o bla-users.csv -r -v domain.com\n\n'
      ' Log into Google Apps domain bla.com as user currently logged into\n'
      ' computer.  Takes CSV file in.csv as input and performs CRUD\n'
      ' operations for user accounts on the domain.  Saves report of CRUD\n'
      ' operations in out.csv. Provide password on command line\n\n'
      '       ./prov.py -i in.csv -o out.csv -p password domain.com\n\n'
      'CSV Field validation rules:\n'
      ' - action, user_name cannot be blank\n\n'
      ' - username, given_name, familiy_name, password required when action\n'
      '   is create\n\n'
      ' - action must be create, update, or delete\n\n'
      ' - ip_whitelisted, suspended, change_pw, admin must be TRUE or FALSE\n'
      '   if no arguement supplied, attribute will be FALSE by default\n\n'
      ' - pw_hash_function must be SHA-1 or MD5\n\n'
      ' - quota_limit is only used in partner edition. Max value is 25600\n\n'
      ' - new_user_name only valid when action is update')

  usage = ('./prov.py [options] domain\n%s' % help_text)

  parser = optparse.OptionParser(usage=usage)
  parser.add_option(
      '-u', '--user', dest='adminuser', action='store', type='string',
      help=('username of domain administrator (default is username you are\n'
            ' using to login to your computer)'))
  parser.add_option(
      '-p', '--password', dest='password', action='store', type='string',
      help='password of domain administrator (will prompt if not provided)')
  parser.add_option(
      '-i', '--input_file', dest='input_file', action='store', type='string',
      help=('input csv file.  Either --INPUT_FILE or --retrieve switch is\n'
            'required'))
  parser.add_option(
      '-v', '--verbose', dest='verbose', action='store_true',
      help='print output to screen')
  parser.add_option(
      '-r', '--retrieve', dest='retrieve', action='store_true',
      help=('retrieve all domain users.  Either --retrieve or --INPUT_FILE\n'
            'switch is required.'))
  parser.add_option(
      '-o', '--output_file', dest='output_file', type='string', action='store',
      help='output_file for logging')
  (options, args) = parser.parse_args()

  if not args:
    parser.print_help()
    sys.exit()
  else:
    domain = args[0]

  if options.adminuser is None:
    options.adminuser = getpass.getuser()
  if options.password is None:
    options.password = getpass.getpass()
  if options.output_file is None:
    options.output_file = 'output.csv'
  if options.retrieve is None and options.input_file is None:
    parser.error('Either --INPUT_FILE or --retrieve swtich required')
  if options.retrieve and options.input_file:
    parser.error('--INPUT_FILE and --retrieve switches cannot be used at\n'
                 'the same time')

  # try to create AppsService object by calling ProvTools with user options
  try:
    app_object = ProvTools('%s@%s' % (options.adminuser, domain),
                           domain, options.password)
    if options.retrieve:
      app_object.GetAllUserInfo(options.output_file, options.verbose)
    else:
      app_object.ProcessCSV(options.input_file, options.verbose,
                            options.output_file)
  except gdata.service.BadAuthentication:
    print 'incorrect username or password for domain %s' % (domain)

if __name__ == '__main__':
  main()
