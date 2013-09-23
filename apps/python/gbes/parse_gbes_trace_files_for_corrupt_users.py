#!/usr/bin/python
#
# Copyright 2010 Google Inc. All Rights Reserved.

"""Prints corrupted users from a directory of GBES Trace files.

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

Given a directory with Trace files from the BlackBerry Connector,
this program searches for error codes related to corruption, then attempts
to pull out the user affected.  This helps determine the scope of the
corruption.

NOTE: This script searches for the code 80040119 only.

Usage:

Options:
  -h, --help         show this help message and exit
  -d TRACE_FILE_DIR  The path to the directory holding the Trace files.

"""

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'

import commands
from optparse import OptionParser
import re
import sys


def ParseInputs():
  """Interprets command line parameters and checks for required parameters."""
  usage = 'parse_gbes_trace_files_for_corrupt_users.py [-d <trace_file_dir>]'
  parser = OptionParser(usage=usage)
  parser.add_option('-d', dest='trace_file_dir', default='.',
                    help="""Path to the directory holding the Trace files.""")

  (options, unused_args) = parser.parse_args()

  return options


def FindCorruptUser(line):
  """Reports a username from a log line containing corruption codes."""

  user_regex = re.compile(r'\((.*?@.*?)\)', re.I)
  corrupt_regex = re.compile(r'80040119')

  user = None

  corrupt_match = re.search(corrupt_regex, line)
  if corrupt_match:
    match_object = re.search(user_regex, line)
    if match_object:
      user = match_object.group(1)

  return user


def ListTraceFiles(trace_file_dir):
  """Returns a list of Trace files from a given directory."""

  ls_cmd = 'ls %s/Trace*.log' % trace_file_dir
  status, text = commands.getstatusoutput(ls_cmd)
  if status != 0:
    print 'ERROR: %s' % text
    sys.exit(1)
  else:
    file_list = text.split('\n')
    return file_list


def main():
  options = ParseInputs()

  print 'INFO: Searching Trace files in directory [%s]' % options.trace_file_dir

  users_with_corruption = []

  for trace_file in ListTraceFiles(options.trace_file_dir):
    f = open(trace_file, 'r')

    for line in f:
      corrupt_user = FindCorruptUser(line)
      if corrupt_user:
        users_with_corruption.append(corrupt_user)

  if users_with_corruption:
    print 'INFO: Corrupted user list:'
    unique_users_with_corruption = set(users_with_corruption)
    for corrupt_user in sorted(unique_users_with_corruption):
      print corrupt_user
  else:
    print 'No corrupted users detected.'


if __name__ == '__main__':
  main()
