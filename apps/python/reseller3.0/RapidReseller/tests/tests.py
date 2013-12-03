#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.

"""
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
   """

__author__ = 'richieforeman@google.com (Richie Foreman)'


import unittest
import webapp2
import main
from mock import patch

from google.appengine.ext import db
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub()

    def tearDown(self):
        self.testbed.deactivate()

class Test_Index(BaseTestCase):
    def test_indexpage(self):
        # it should draw the main index page.
        request = webapp2.Request.blank('/')

        with patch('app.BaseHandler.render_template') as template:
            response = request.get_response(main.wsgi)
            template.assert_called_with('templates/index.html')

        self.assertEqual(response.status_int, 200)

class Test_Step1(BaseTestCase):
    def test_get(self):
        # it should fetch the time and build a temporary domain name.
        request = webapp2.Request.blank('/step1')

        with patch('app.BaseHandler.render_template') as template, \
            patch('time.time', return_value="123") as time_mock:
            response = request.get_response(main.wsgi)

            template.assert_called_with(
                "templates/step1.html",
                domain="demo-123.resold.richieforeman.net")

        self.assertEqual(response.status_int, 200)

    def test_post(self):
        request = webapp2.Request.blank("/step1", POST={
            'domain': 'demo-123.resold.richieforeman.net'
        })

        response = request.get_response(main.wsgi)


if __name__ == '__main__':
    unittest.main()
