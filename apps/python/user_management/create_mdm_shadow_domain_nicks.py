#!/usr/bin/python
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the Licens

"""Applies nicknames for a list of shadow domains for all users in the domain.

   Given a list of domain pairs, this program will make sure all
   provisioned users in the first domain have nicknames in the second.

   This program can be run in two modes:  dry run mode and live mode.  Dry run
   mode will only report the changes it would have made but will not make them.
   This is the default behavior.  If the user wants the changes to be made,
   use the --apply flag to run the program in live mode.

   Usage: create_mdm_shadow_domain_nicks.py

   Options:
     -h, --help      show this help message and exit
     -u ADMIN_USER   admin user
     -p ADMIN_PASS   admin pass
     -d DOMAIN       Domain name                               # optional
     -n NICK_DOMAIN  The domain of the nick that should exist. # optional
     --apply         If present, changes will be applied, otherwise will run
                              in dry run mode with no changes made

   Typical Usage:
     a) Dry run:   create_mdm_shadow_domain_nicks.py -u admin@primary.com -p PASS
     a) Live Mode: create_mdm_shadow_domain_nicks.py -u admin@primary.com -p PASS --apply
"""

# If you have multiple domain pairs uncomment this dict and add them
# in key/value form

# Add domain pairs, user domain first, shadow domain second
#DOMAIN_PAIRS = {'mdauphin.info':         'mdm.mdauphinee.info',
#                'subco.mdauphinee.info': 'shadow.subco.mdauphinee.info'}
DOMAIN_PAIRS = {}


__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import datetime
import gdata.apps.service as apps_service
import httplib
import logging
import sys
import urllib

from optparse import OptionParser


class Logger:
  """Object to allow logging to file and printing to screen."""

  def __init__(self):
    self.log_filename = 'create_mdm_shadow_domain_nicks_%s.log' % GetTimeStamp()
    logging.basicConfig(filename=self.log_filename, level=logging.DEBUG)

  def LogPrintError(self, msg):
    logging.error(msg)
    print msg

  def LogPrintInfo(self, msg):
    logging.info(msg)
    print msg

  def GetLogFilename(self):
    return self.log_filename


class NickManager:
  """Class to find missing nicks and create them."""

  def __init__(self, admin_user, admin_pass, primary_domain,
               nick_domain, logger):
    self.primary_domain_connect = apps_service.AppsService(email=admin_user,
                                                           domain=primary_domain,
                                                           password=admin_pass)
    self.primary_domain_connect.ProgrammaticLogin()
    self.nick_domain_connect = apps_service.AppsService(email=admin_user,
                                                        domain=nick_domain,
                                                        password=admin_pass)
    self.nick_domain_connect.ProgrammaticLogin()
    self.nicknames = []
    self.user_addresses = []
    self.admin_user = admin_user
    self.admin_pass = admin_pass
    self.primary_domain = primary_domain
    self.nick_domain = nick_domain
    self.logger = logger

  def GetMissingNicks(self):
    self.nicknames = self._GetAllNicks()
    self.user_addresses = self._GetProvisionedUsers()
    return list(set(self.user_addresses).difference(set(self.nicknames)))

  def CreateMissingNicks(self, nicklist):
    auth_token = self._GetAuthToken()
    alias_url = ('https://apps-apis.google.com/a/feeds/alias/2.0/%s/' %
                 (self.nick_domain))
    for nick in nicklist:
      xml_template = """<atom:entry xmlns:atom='http://www.w3.org/2005/Atom' xmlns:apps='http://schemas.google.com/apps/2006'>
                         <apps:property name="aliasEmail" value="%s@%s" />
                         <apps:property name="userEmail" value="%s@%s" />
                       </atom:entry>\n\n""" % (nick, self.nick_domain, nick, self.primary_domain)
      headers = {'Content-type': 'application/atom+xml',
                 'Authorization': '%s%s' % ('GoogleLogin auth=', auth_token)}
      self.logger.LogPrintInfo('Creating nick %s@%s' % (nick, self.nick_domain))
      try:
        connection = httplib.HTTPSConnection('apps-apis.google.com')
        connection.set_debuglevel(0)
        connection.request('POST', alias_url, xml_template, headers)
        response = connection.getresponse()
        if response.status == 201:
          self.logger.LogPrintInfo(('%s@%s alias added for user %s@%s successfully' %
                                    (nick, self.nick_domain, nick, self.primary_domain)))
        else:
          self.logger.LogPrintError(('Alias creation was not successful.  Status: %s : %s' %
                                     (response.status, response.read())))
      except Exception, e:
        self.logger.LogPrintError('Failed to create nick %s@%s: %s' % (nick, self.nick_domain, str(e)))

  def _GetProvisionedUsers(self):
    users = []
    user_feed = self.primary_domain_connect.RetrieveAllUsers()
    for user_entry in user_feed.entry:
      users.append(user_entry.login.user_name.lower())
    return users

  def _GetAllNicks(self):
    nicks = []
    nick_feed = self.nick_domain_connect.RetrieveAllNicknames()
    for nick_entry in nick_feed.entry:
      nicks.append(nick_entry.nickname.name)
    return nicks

  def _GetAuthToken(self):

    url = 'https://www.google.com/accounts/ClientLogin'
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    values = {'Email': self.admin_user,
              'Passwd': self.admin_pass,
              'accountType': 'HOSTED',
              'service': 'apps'}
    data = urllib.urlencode(values)
    try:
      connection = httplib.HTTPSConnection('www.google.com')
      connection.set_debuglevel(0)
      connection.request('POST', url, body=data, headers=headers)
      response = connection.getresponse()
      response = response.read()
    except Exception, e:
      self.logger.LogPrintError(
          'Could not connect to client login: %s' % str(e))
      sys.exit(10)

    # auth_token is the substring between 'Auth=' and the end of response string
    return response[response.index('Auth=')+5:len(response)]


def ParseInputs():
  global DOMAIN_PAIRS

  usage = """usage: %prog -d <domain> -u <admin_user> -p <admin_pass>\n"""
  parser = OptionParser()
  parser.add_option("-u", dest="admin_user", help="admin user")
  parser.add_option("-p", dest="admin_pass", help="admin pass")
  parser.add_option("-d", dest="domain", help="Domain name")
  parser.add_option("-n", dest="nick_domain",
                    help="The domain of the nick that should exist.",)
  parser.add_option("--apply", action="store_true", dest="apply",
                    help="""If present, changes will be applied, otherwise
                            will run in dry run mode with no changes made""")

  (options, args) = parser.parse_args()

  if options.admin_user is None:
    print "-u (admin user) is required"
    sys.exit(1)
  if options.admin_pass is None:
    print "-p (admin password) is required"
    sys.exit(1)
  if (options.domain and not options.nick_domain) or (options.nick_domain and not options.domain):
    print "Both -d and -n need to be given"
    sys.exit(1)
  if not options.domain and not options.nick_domain and not DOMAIN_PAIRS:
    print "No domain pairs given"
    sys.exit(1)

  return options


def GetTimeStamp():
  now = datetime.datetime.now()
  return now.strftime("%Y%m%d%H%M%S")


def main():

  global DOMAIN_PAIRS

  options = ParseInputs()

  # Set up logging
  logger = Logger()

  if not options.apply:
    logger.LogPrintInfo('RUNNING IN DRY RUN MODE..\t')

  if options.domain:
    DOMAIN_PAIRS = {options.domain: options.nick_domain}

  for domain, shadow_domain in DOMAIN_PAIRS.items():


    logger.LogPrintInfo('Creating nicknames for domain pair [%s : %s]' % (domain, shadow_domain))
    nick_manager = NickManager(options.admin_user, options.admin_pass,
                               domain, shadow_domain, logger)

    missing_nicks = nick_manager.GetMissingNicks()
    logger.LogPrintInfo('%d missing nicks found' % len(missing_nicks))

    if options.apply:
      nick_manager.CreateMissingNicks(missing_nicks)
    else:
      for nick in missing_nicks:
        logger.LogPrintInfo(
            """DRY RUN MODE: Would have created nickname %s@%s for user %s@%s""" %
            (nick, shadow_domain, nick, domain))

  print 'Log File is: %s' % logger.GetLogFilename()


if __name__ == '__main__':
  main()
