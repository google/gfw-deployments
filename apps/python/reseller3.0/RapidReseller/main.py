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

"""
    This simple Python AppEngine demonstrates the workflow for
    provisioning a resold customer, step-by-step

    With minor modifications, this code could be ported to another language,
    or alternatively deployed on a traditional server.

    Setup:
    - Install the AppEngine SDK.
    - Install the Google API Python Client
      (https://code.google.com/p/google-api-php-client/)
    - Generate an OAuth2 project.
      ( https://code.google.com/apis/console/ )
    - From the services tab, activate the following:
        "Google Apps Reseller API"
        "Admin SDK"
        "Site Verification API"
    - Add a new API Client ID from the console
      - Select the service account mechanism
      - Download the p12 private key.
    - Convert the P12 key into PEM format:
        "openssl pkcs12 -in xxxxx.p12 -nodes -nocerts > privatekey.pem"
    - Adjust 'settings.py' to reflect the API Client ID,
      Service Account Email Address, and private key location.
    - Authorize the Client ID in the Google Apps Control Panel
      for the reseller domain.
      ( Security -> Advanced Settings -> Manage Third Party OAuth )

      For the client name, utilize the Client ID from the API project.

      Add the following scopes:
        https://www.googleapis.com/auth/apps.order
        https://www.googleapis.com/auth/siteverification
        https://apps-apis.google.com/a/feeds/user/
        https://www.googleapis.com/auth/admin.directory.user
"""

from apiclient.discovery import build
from google.appengine.api import taskqueue
import httplib2
import logging
import time
import webapp2

from app import BaseHandler

from constants import ResellerPlanName
from constants import ResellerSKU
from constants import ResellerRenewalType
from constants import ResellerProduct

import settings

from utils import get_authorized_http
from utils import csrf_protect

class IndexHandler(BaseHandler):

    def get(self):
        return self.render_template("templates/index.html")


class StepOneHandler(BaseHandler):
    def get(self):

        # generate a bogus domain name for demo purposes.
        domain = settings.DOMAIN_TEMPLATE % int(time.time())

        return self.render_template("templates/step1.html",
                                    domain=domain)

    @csrf_protect
    def post(self):
        domain = self.request.get('domain')

        service = build(serviceName="reseller",
                        version=settings.RESELLER_API_VERSION,
                        http=get_authorized_http())

        method = service.customers().insert(body={
            'customerDomain': domain,
            'alternateEmail': 'nobody@google.com',
            'phoneNumber': '212.565.0000',
            'postalAddress': {
                'contactName': "A Googler",
                'organizationName': 'Google, Inc',
                'locality': 'New York City',
                'countryCode': 'US',
                'region': 'NY',
                'postalCode': '10011',
                'addressLine1': '76 9th Ave'
            }
        }).execute()

        self.session['domain'] = domain

        # Mark the domain for deletion in approx 5 days.
        taskqueue.add(url="/tasks/cleanup",
                      name="cleanup__%s" % domain.replace(".", "_"),
                      countdown=settings.DOMAIN_CLEANUP_TIMER,
                      params={
                          'domain': domain
                      })

        return self.redirect("/step2")


class StepTwoHandler(BaseHandler):
    def get(self):
        return self.render_template("templates/step2.html")

    @csrf_protect
    def post(self):
        service = build(serviceName="reseller",
                        version=settings.RESELLER_API_VERSION,
                        http=get_authorized_http())

        response = service.subscriptions().insert(
            customerId=self.session['domain'],
            body={
                'customerId': self.session['domain'],
                'subscriptionId': "%s-apps" % self.session['domain'],
                'skuId': ResellerSKU.GoogleApps,
                'plan': {
                    'planName': ResellerPlanName.Flexible,
                    'isCommitmentPlan': False,
                },
                'seats': {
                    'numberOfSeats': self.request.get("seats"),
                    'maximumNumberOfSeats': self.request.get("seats")
                },
                'renewalSettings': {
                    'renewalType': ResellerRenewalType.PayAsYouGo
                },
                'purchaseOrderId': 'G00gl39001'
            }).execute(num_retries=5)

        return self.redirect("/step3")


class StepThreeHandler(BaseHandler):
    def get(self):
        '''
        Prompt the user to select a verification method.
        '''
        return self.render_template("templates/step3.html")

    @csrf_protect
    def post(self):
        '''
        Call the site verification api and fetch the token value.
        '''

        # establish default values.
        verification_type = "INET_DOMAIN"
        identifier = self.session['domain']
        verification_method = self.request.get("verificationMethod")

        # Does the requested verification method fall into the "site" type?
        if verification_method in settings.SITE_VERIFICATION_METHODS:
            # a "site" type is chosen, the values are a different.
            verification_type = "SITE"
            # site verification methods must begin with http or https
            identifier = "http://%s" % self.session['domain']

        # build the site verification service.
        service = build(serviceName="siteVerification",
                        version="v1",
                        http=get_authorized_http())

        # fetch a verification token.
        response = service.webResource().getToken(body={
            'site': {
                'type': verification_type,
                'identifier': identifier
            },
            'verificationMethod': verification_method
        }).execute(num_retries=5)

        return self.render_template("templates/step3_confirm.html",
                                    verification_token=response['token'],
                                    verification_type=verification_type,
                                    verification_method=verification_method,
                                    verification_identifier=identifier)


class StepFourHandler(BaseHandler):
    def get(self):
        '''
        Call the site verification service and see if the
        token has been fulfilled (e.g. a dns entry added)
        '''

        service = build(serviceName="siteVerification",
                        version="v1",
                        http=get_authorized_http())

        verification_type = self.request.get("verification_type")
        verification_ident = self.request.get("verification_identifier")
        verification_method = self.request.get("verification_method")

        verification_status = None
        try:
            # try to do a verification,
            # which will test the method on the Google server side.
            service.webResource().insert(
                verificationMethod=verification_method,
                body={
                    'site': {
                        'type': verification_type,
                        'identifier': verification_ident
                    },
                    'verificationMethod': verification_method
                }
            ).execute(num_retries=5)
            verification_status = True
        except Exception, e:
            verification_status = False

        return self.render_template("templates/step4.html",
                                    verification_status=verification_status)


class StepFiveHandler(BaseHandler):

    def get(self):
        return self.render_template("templates/step5.html")

    @csrf_protect
    def post(self):
        username = "admin@%s" % self.session['domain']
        password = "P@ssw0rd!!"

        service = build(serviceName="admin",
                        version="directory_v1",
                        http=get_authorized_http())

        # create the user.
        service.users().insert(body={
            'primaryEmail': username,
            'name': {
                'givenName': 'Admin',
                'familyName': 'Admin',
                'fullName': 'Admin Admin'
            },
            'suspended': False,
            'password': password
        }).execute(num_retries=5)

        # make the user a super admin.
        service.users().makeAdmin(
            userKey=username,
            body={
                'status': True
            }).execute(num_retries=5)

        self.session['username'] = username

        return self.render_template("templates/step5_confirm.html",
                                    domain=self.session['domain'],
                                    username=username,
                                    password=password)


class StepSixHandler(BaseHandler):
    def get(self):
        return self.render_template("templates/step6.html")

    @csrf_protect
    def post(self):
        service = build(serviceName="reseller",
                        version=settings.RESELLER_API_VERSION,
                        http=get_authorized_http())

        response = service.subscriptions().insert(
            customerId=self.session['domain'],
            body={
                'customerId': self.session['domain'],
                'skuId': ResellerSKU.GoogleDriveStorage20GB,
                'plan': {
                    'planName': ResellerPlanName.Flexible
                },
                'seats': {
                    'numberOfSeats': 5,
                    'maximumNumberOfSeats': 5,
                },
                'purchaseOrderId': 'G00gl39001-d20'
            }).execute(num_retries=5)

        return self.redirect("/step7")


class StepSevenHandler(BaseHandler):
    def get(self):
        return self.render_template("templates/step7.html")

    @csrf_protect
    def post(self):
        service = build(serviceName="licensing",
                        version='v1',
                        http=get_authorized_http())

        service.licenseAssignments().insert(
            productId=ResellerProduct.GoogleDrive,
            skuId=ResellerSKU.GoogleDriveStorage20GB,
            body={
                'userId': 'admin@%s' % self.session['domain']
            }).execute(num_retries=5)

        return self.render_template("templates/fin.html")


app = webapp2.WSGIApplication(routes=[
    (r'/', IndexHandler),
    (r'/step1', StepOneHandler),
    (r'/step2', StepTwoHandler),
    (r'/step3', StepThreeHandler),
    (r'/step4', StepFourHandler),
    (r'/step5', StepFiveHandler),
    (r'/step6', StepSixHandler),
    (r'/step7', StepSevenHandler)
], config=settings.WEBAPP2_CONFIG)