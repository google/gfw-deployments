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

import os

from google.appengine.api import users
import jinja2
import logging
import traceback
from uuid import uuid4
import webapp2
from webapp2_extras import sessions

import settings


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # activate session store.
        self.session_store = sessions.get_store(request=self.request)

        # dispatch handler.
        out = webapp2.RequestHandler.dispatch(self)
        self.response.out.write(out)

        # save session.
        self.session_store.save_sessions(self.response)

    def get_csrf_token(self):
        token = self.session.get('csrf_token', None)

        if token is None:
            token = uuid4().hex
            self.session['csrf_token'] = token

        return token

    def regen_csrf_token(self):
        token = uuid4().hex
        self.session['csrf_token'] = token
        return token

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(backend=settings.SESSION_BACKEND,
                                              max_age=settings.SESSION_MAXAGE)

    @webapp2.cached_property
    def jinja(self):
        path = os.path.dirname(os.path.realpath(__file__))

        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(path))

    def handle_exception(self, exception, debug):
        self.response.set_status(500)
        logging.exception(exception)
        return self.render_template("templates/_exception.html",
                                    exception=traceback.format_exc())

    def render_template(self, template, **kwargs):
        '''
        Render a Jinja Template, taking template variables as **kwargs
        :param t:
        :param kwargs:
        :return:
        '''

        # inject some template variables
        kwargs.update({
            "url": self.request.url,
            "path": self.request.path,
            "settings": settings,
            "user": users.get_current_user(),
            "is_admin": users.is_current_user_admin(),
            "os_environ": os.environ,
            '_csrf_token_': self.get_csrf_token()
        })

        return self.jinja.get_template(template).render(**kwargs)


