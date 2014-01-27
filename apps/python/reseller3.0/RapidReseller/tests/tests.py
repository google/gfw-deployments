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
from apiclient.http import HttpMock
import json
from apiclient.http import HttpMockSequence
import os
TEST_ROOT = os.path.dirname(os.path.realpath(__file__))
RESELLER_DISCOVERY = open(TEST_ROOT + '/data/reseller_v1.json', 'rb').read()

app = main.app
app._ENABLE_CSRF = False

RESELLER_DISCOVERY_URL = "https://www.googleapis.com/discovery/v1/apis/reseller/v1/rest"
class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_taskqueue_stub()

    def tearDown(self):
        self.testbed.deactivate()

class Test_Index(BaseTestCase):
    def test_indexpage(self):
        # it should draw the main index page.
        request = webapp2.Request.blank('/')

        with patch('app.BaseHandler.render_template') as template:
            response = request.get_response(app)
            template.assert_called_with('templates/index.html')

        self.assertEqual(response.status_int, 200)

class Test_Step1(BaseTestCase):
    def test_get(self):
        # it should fetch the time and build a temporary domain name.
        request = webapp2.Request.blank('/step1')

        with patch('app.BaseHandler.render_template') as template, \
            patch('time.time', return_value="123") as time_mock:
            response = request.get_response(main.app)

            template.assert_called_with(
                "templates/step1.html",
                domain="demo-123.resold.richieforeman.net")

        self.assertEqual(response.status_int, 200)

    def test_post(self):
        request = webapp2.Request.blank("/step1", POST={
            'domain': 'demo-123.resold.richieforeman.net'
        })
        from mock import MagicMock

        http = HttpMockSequence([
            ({'status': '200'}, RESELLER_DISCOVERY),
            ({'status': '200'}, json.dumps({}))
        ])

        # wrap http.request so we can spy on it.
        http.request = MagicMock(wraps=http.request)

        with patch('main.get_authorized_http', return_value=http):
            response = request.get_response(app)

            self.assertTrue(http.request.called)
            discovery_call = http.request.call_args_list[0]
            create_customer = http.request.call_args_list[1]

            # ensure that a discovery call occured.
            (url,), args = discovery_call
            self.assertEqual(url, RESELLER_DISCOVERY_URL)

            # ensure that a customer was created via the POST api.
            (url, method), args = create_customer
            self.assertEqual(url, 'https://www.googleapis.com/apps/reseller/v1/customers?alt=json')
            self.assertEqual(method, 'POST')


if __name__ == '__main__':
    unittest.main()
