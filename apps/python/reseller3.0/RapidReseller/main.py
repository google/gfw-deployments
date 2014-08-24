#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.

__author__ = 'richieforeman@google.com (Richie Foreman)'

from app import BaseHandler
from app import WSGIApplication

import buyflow

import settings

class IndexHandler(BaseHandler):
  def get(self):
    # draw the initial baseline template.
    self.response.out.write(self.render_template("templates/base.html"))

app = WSGIApplication(routes=[
  # Reseller Buy Flow API Methods
  (r'/api/createCustomer', buyflow.CreateCustomerHandler),
  (r'/api/createSubscription', buyflow.CreateSubscriptionHandler),
  (r'/api/getSiteValidationToken', buyflow.GetSiteVerificationTokenHandler),
  (r'/api/testValidation', buyflow.VerifySiteHandler),
  (r'/api/createUser', buyflow.CreateAdminUserHandler),
  # Generic Template Method.
  (r'/.*', IndexHandler)
], config=settings.WEBAPP2_CONFIG)
