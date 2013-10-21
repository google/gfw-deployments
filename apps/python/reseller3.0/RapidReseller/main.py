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

import time

from app import wsgi
from app import BaseHandler

from constants import ResellerPlanName
from constants import ResellerSKU
from constants import ResellerRenewalType

import settings

from apiclient.discovery import build

from gdata.apps.client import AppsClient
from gdata.gauth import OAuth2TokenFromCredentials

import httplib2
from oauth2client.client import SignedJwtAssertionCredentials

def get_credentials(sub=None):
    '''
    Signed JWT Credentials allow for frictionless authentication
    using a private key as opposed to a three-legged oauth flow.
    '''
    f = file(settings.OAUTH2_PRIVATEKEY)
    key = f.read()
    f.close()

    # establish the credentials.
    credentials = SignedJwtAssertionCredentials(
        service_account_name=settings.OAUTH2_SERVICE_ACCOUNT_EMAIL,
        private_key=key,
        scope=" ".join(settings.OAUTH2_SCOPES),
        sub=sub)

    return credentials


@wsgi.route("/")
class IndexHandler(BaseHandler):
    def get(self):
        return self.render_template("templates/index.html")

@wsgi.route("/step1")
class StepOneHandler(BaseHandler):
    def get(self):

        # generate a bogus domain name for demo purposes.
        domain = "demo-%d.gappslabs.co" % int(time.time())

        return self.render_template("templates/step1.html",
                                    domain=domain)

    def post(self):

        credentials = get_credentials(settings.RESELLER_ADMIN)

        http = httplib2.Http()
        credentials.authorize(http)

        service = build(serviceName="reseller",
                        version=settings.RESELLER_API_VERSION,
                        http=http)

        response = service.customers().insert(body={
            'customerDomain': self.request.get("domain"),
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
        }).execute(num_retries=5)

        self.session['domain'] = self.request.get('domain')
        return self.redirect("/step2")

    @wsgi.route("/step2")
    class StepTwoHandler(BaseHandler):
        def get(self):
            return self.render_template("templates/step2.html")

        def post(self):

            credentials = get_credentials(settings.RESELLER_ADMIN)

            http = httplib2.Http()
            credentials.authorize(http)

            service = build(serviceName="reseller",
                            version=settings.RESELLER_API_VERSION,
                            http=http)

            response = service.subscriptions().insert(
                customerId=self.session['domain'],
                body={
                    'customerId': self.session['domain'],
                    'subscriptionId': "%s-apps" % self.session['domain'],
                    'skuId': ResellerSKU.GoogleApps,
                    'plan': {
                        'planName': ResellerPlanName.Trial,
                        'isCommitmentPlan': False,
                        'commitmentInterval': {
                            'startTime': int(time.time()),
                            # have the trial end 15 days later.
                            'endTime': int(time.time()) + (86400 * 15)
                        }
                    },
                    'seats': {
                        'numberOfSeats': self.request.get("seats"),
                        'maximumNumberOfSeats': self.request.get("seats")
                    },
                    'renewalSettings': {
                        'renewalType': ResellerRenewalType.AutoRenew
                    },
                    'purchaseOrderId': 'G00gl39001'
                }).execute(num_retries=5)

            return self.redirect("/step3")

    @wsgi.route("/step3")
    class Step3Handler(BaseHandler):
        def get(self):
            return self.render_template("templates/step3.html")

        def post(self):
            credentials = get_credentials(settings.RESELLER_ADMIN)

            http = httplib2.Http()
            credentials.authorize(http)

            # establish default values.
            verification_type = "INET_DOMAIN"
            identifier = self.session['domain']
            verification_method = self.request.get("verificationMethod")

            # Does the requested verification method fall into the "site" type?
            if verification_method in settings.SITE_VERIFICATION_METHODS:
                # a "site" type is chosen, the values are a different.
                verification_type = "SITE"
                identifier = "http://%s" % self.session['domain']

            # build the site verification service.
            service = build(serviceName="siteVerification",
                            version="v1",
                            http=http)

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

    @wsgi.route("/step4")
    class Step4Handler(BaseHandler):
        def get(self):
            credentials = get_credentials(settings.RESELLER_ADMIN)

            http = httplib2.Http()
            credentials.authorize(http)

            service = build(serviceName="siteVerification",
                            version="v1",
                            http=http)

            verification_type = self.request.get("verification_type")
            verification_identifier = self.request.get("verification_identifier")
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
                            'identifier': verification_identifier
                        },
                        'verificationMethod': verification_method
                    }
                ).execute(num_retries=5)
                verification_status = True
            except:
                verification_status = False

            return self.render_template("templates/step4.html",
                                        verficiation_status=verification_status)

    @wsgi.route("/step5")
    class StepFiveHandler(BaseHandler):

        def get(self):
            return self.render_template("templates/step5.html")

        def post(self):

            # establish the credentials.
            credentials = get_credentials(sub=settings.RESELLER_ADMIN)

            http = httplib2.Http()
            credentials.authorize(http)
            # force a refresh so we can pull out the Bearer token.
            credentials.refresh(http=http)

            client = AppsClient(
                domain=self.session['domain'],
                auth_token=OAuth2TokenFromCredentials(credentials))

            client.ssl = True

            user = client.CreateUser(user_name="admin",
                                     given_name="Admin",
                                     family_name="Admin",
                                     password="P@ssw0rd!!",
                                     suspended="false",
                                     admin="true")

            return self.render_template(
                "templates/step5_confirm.html",
                domain=self.session['domain'],
                username="admin@%s" % self.session['domain'],
                password="P@ssw0rd!!")