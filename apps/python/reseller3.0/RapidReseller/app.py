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

import logging


from google.appengine.api import users
import settings
import jinja2
import traceback
import webapp2
from webapp2_extras import sessions


class WSGIApplication(webapp2.WSGIApplication):

    def route(self, uri):
        '''
        Class decorator for defining a route.
        '''
        def wrapper(func):
            self.router.add(webapp2.Route(uri, handler=func))
            return func

        return wrapper


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        out = webapp2.RequestHandler.dispatch(self)
        self.response.out.write(out)

        self.session_store.save_sessions(self.response)

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
            "os_environ": os.environ
        })

        return self.jinja.get_template(template).render(**kwargs)


wsgi = WSGIApplication(config=settings.WEBAPP2_CONFIG)