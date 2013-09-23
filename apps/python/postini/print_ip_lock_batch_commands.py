#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Utility to print Postini IP Lock batch commands.

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

 In order to whitelist intradomain mail for Google Apps customers
 which use Postini, a typical implementation is to add the domain
 to the Approved Senders list for the Account in Postini in conjunction
 with using IP Lock at the Postini level to restrict which IPs can
 legitimately send on behalf of that domain.

 IP Lock Documentation:
  - http://www.postini.com/webdocs/admin_ee_cu/wwhelp/wwhimpl/common/html/wwhelp.htm?context=EEHelp&file=secur_iplock.html

 This script outputs IP Lock batch commands for every combination of the
 given:
  - domains
  - Email Configs
  - Legitimate sending IP addresses/ranges

 An administrator can then customize the commands as they see fit
 and consider copy/pasting the commands into Postini's Admin console
 to implement the IP Lock.

  USAGE:
          - Edit the DOMAINS, EMAIL_CONFIGS, and ALLOWED_IPS python lists
            to reflect the proper values for your situation.
          - Run this script and output to a file:
              > run: print_ip_lock_batch_commands.py > ip_lock_commands.txt
          - Customize the outputted batch commands for your environment
          - These commands can then be used in the batch section of the
            Postini Admin console

"""

import sys

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

# Add all domains here
DOMAINS = [
           'domain.com',
           'otherdomain.com',
          ]

# Add all Email Configs here
EMAIL_CONFIGS = [
                 'GApps Mail Config',
                 'Second Exchange Server Config'
                ]

# Add all IPs that legitimately send on behalf of the given DOMAINS
# Make sure to include GMail IPs if appropriate by using the ranges
# given from > dig txt _spf.google.com
ALLOWED_IPS = ['66.344.138.81',
               '216.239.32.0/19',
               '64.233.160.0/19',
               '66.249.80.0/20',
               '72.14.192.0/18',
               '209.85.128.0/17',
               '66.102.0.0/20',
               '74.125.0.0/16',
               '74.125.0.0/16',
               '207.126.144.0/20',
               '173.194.0.0/16']


def CheckLimitViolation():
  """Warns user if IP Lock character limit will be breached."""

  for ec in EMAIL_CONFIGS:
    domain_list_prefix = ','.join(DOMAINS) + ':'
    ip_lock_string = ''
    for ip in ALLOWED_IPS:
      ip_lock_string += domain_list_prefix + ip + '\n'
    if len(ip_lock_string) > 4000:
      print 'Org: [%s]' % ec
      print ip_lock_string
      print 'ERROR: IP Lock character limit breached'
      print 'Potential length: [%d]' % len(ip_lock_string)
      print '\n\nPostini restricts the character length IP length to 4000 characters.'
      print 'and you have gone over for the [%s] Org' % ec
      print 'You will need to shrink the number of IPs for an Org and retry'
      print 'See IP Lock documentation at: %s' % 'http://www.postini.com/webdocs/admin_ee_cu/wwhelp/wwhimpl/common/html/wwhelp.htm?context=EEHelp&file=secur_iplock.html'
      sys.exit(2)


def main():

  CheckLimitViolation()

  for ec in EMAIL_CONFIGS:
    for d in DOMAINS:
      for aip in ALLOWED_IPS:
        print 'addallowedip %s,%s:%s' % (ec, d, aip)



if __name__ == '__main__':
  main()
