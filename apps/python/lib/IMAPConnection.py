#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.
"""
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


This library contains functions for connecting to and interfacing with a
Gmail account using IMAP. It is not comprehensive in the functionality it
offers.
"""

import imaplib
import time

from datetime import datetime

# The longest period of time during which an open IMAP connection should be
# reused, in seconds.
IMAP_CONNECTION_MAX_DURATION = 300


class IMAPConnection(object):
  def __init__(self, imap_debug=0, xoauth_string=''):
    self.imap_debug = imap_debug
    self.xoauth_string = xoauth_string

    self.connection = None
    self.connection_start = datetime(1, 1, 1)
    self.label = None

  def _Connect(self):
    self.connection_start = datetime.now()
    self.connection = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    self.connection.debug = self.imap_debug

    try:
      self.connection.authenticate('XOAUTH', lambda x: self.xoauth_string)
    except Exception, e:
      return

    if self.label:
      self.connection.select(self.label)

  def Close(self):
    try:
      self.connection.close()
      self.connection.logout()
    except Exception, e:
      self.connection = None

  def _CheckRefresh(self):
    if ((datetime.now() - self.connection_start).seconds >
        IMAP_CONNECTION_MAX_DURATION):
      self.Close()
      self._Connect()

  def GetMessageLocatorsInLabel(self, label, query):
    self._CheckRefresh()

    try:
      (result, unused_data) = self.connection.select(label)
    except Exception, e:
      return []
 
    self.label = label

    unused_type, data = self.connection.uid('SEARCH', 'X-GM-RAW', query)

    return data[0].split()

  def List(self):
    self._CheckRefresh()

    try:
      (unused_data, list) = self.connection.list()
    except Exception, e:
      list = []

    return list
    
  def GetMessage(self, message_locator):
    self._CheckRefresh()

    remaining_tries = 4
    while remaining_tries >= 0:
      try:
        (result, message_info) = self.connection.uid('FETCH', message_locator,
                                                     '(RFC822)')

        remaining_tries = -1
      except Exception, e:
        if remaining_tries == 0:
          raise
        remaining_tries -= 1
        time.sleep(3)
        self.Close()
        self._Connect()

    message = ''
    if message_info:
      try:
        (unused_data, message) = message_info[0]
      except Exception, e:
        return ''

    return message

  def AddLabel(self, message_locator, label):
    self._CheckRefresh()

    try:
      self.connection.uid('COPY', message_locator, label)
      self.connection.expunge()
      return True
    except Exception, e:
      return False

  def CreateLabel(self, label):
    self._CheckRefresh()

    try:
      self.connection.create(label)
      return True
    except Exception, e:
      return False
