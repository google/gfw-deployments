#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.
"""
    Base handlers and core application components

        WSGIApplication: Extended from webapp2.WSGIApplication
        BaseHandler: Basic webapp2 request handler, with templating and XSRF
        ApiHandler: Basic webapp2 request handler for serving a simple JSON API

"""

"""
   DISCLAIMER:

   (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
   WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
   WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
   PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND

   (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA
   , OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
   DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
   GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
   THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR
   ITS DERIVATIVES.
"""

__author__ = 'richieforeman@google.com (Richie Foreman)'

from apiclient.http import HttpError
import logging
import json
from oauth2client.appengine import xsrf_secret_key
from oauth2client import xsrfutil
import settings
from uuid import uuid4
import webapp2
from webapp2_extras import sessions


class WSGIApplication(webapp2.WSGIApplication):
    _ENABLE_CSRF = True


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # activate session store.
        self.session_store = sessions.get_store(request=self.request)

        # dispatch handler.
        out = webapp2.RequestHandler.dispatch(self)

        # Let angular know about our XSRF-TOKEN
        self.response.set_cookie("XSRF-TOKEN", self.get_csrf_token())

        # save session.
        self.session_store.save_sessions(self.response)

        return out

    def get_csrf_token(self):
        token = self.session.get('csrf_token', None)

        if token is None:
            token = self.regenerate_csrf_token()
        return token

    def regenerate_csrf_token(self):
        session_cookie = self.request.cookies.get('session')
        token = xsrfutil.generate_token(xsrf_secret_key(), session_cookie)

        self.session['csrf_token'] = token
        return token

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(backend=settings.SESSION_BACKEND,
                                              max_age=settings.SESSION_MAXAGE)

    def handle_exception(self, exception, debug):
        self.response.set_status(500)
        logging.exception(exception)
        raise exception

    def render_template(self, template, **kwargs):
        return file(template).read()


class ApiHandler(BaseHandler):
    json_data = {}

    def dispatch(self):
        if self.request.body:
            self.json_data = json.loads(self.request.body)

        response = super(ApiHandler, self).dispatch()

        if response:
            self.response.out.write(json.dumps(response))

    def handle_exception(self, exception, debug):
        self.response.set_status(500)

        logging.exception(exception)

        if type(exception) is HttpError:
            data = json.loads(exception.content)
            message = data.get('error', {}).get('message')
        else:
            message = str(exception)

        self.response.out.write(json.dumps({
            'message': message
        }))
