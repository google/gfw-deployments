#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.

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

from apiclient.discovery import build
from apiclient.http import HttpError
from google.appengine.api import taskqueue

from app import ApiHandler
from app import BaseHandler
from app import WSGIApplication

from constants import ResellerPlanName
from constants import ResellerSKU
from constants import ResellerRenewalType
from constants import ResellerProduct

import settings

from utils import get_authorized_http
from utils import csrf_protect


class IndexHandler(BaseHandler):

    def get(self):
        # draw the initial baseline template.
        self.response.out.write(self.render_template("templates/base.html"))


class StepOneHandler(ApiHandler):

    @csrf_protect
    def post(self):
        domain = self.json_data['domain']
        alternate_email = self.json_data['alternateEmail']
        phone_number = self.json_data['phoneNumber']
        contact_name = self.json_data['postalAddress.contactName']
        organization_name = self.json_data['postalAddress.organizationName']
        locality = self.json_data['postalAddress.locality']
        country_code = self.json_data['postalAddress.countryCode']
        region = self.json_data['postalAddress.region']
        postal_code = self.json_data['postalAddress.postalCode']
        address_line_1 = self.json_data['postalAddress.addressLine1']

        service = build(serviceName="reseller",
                        version=settings.RESELLER_API_VERSION,
                        http=get_authorized_http())

        try:
            method = service.customers().get(customerId=domain).execute()
            raise Exception("That customer already exists")
        except HttpError, e:
            if int(e.resp['status']) != 404:
                raise

        method = service.customers().insert(body={
            'customerDomain': domain,
            'alternateEmail': alternate_email,
            'phoneNumber': phone_number,
            'postalAddress': {
                'contactName': contact_name,
                'organizationName': organization_name,
                'locality': locality,
                'countryCode': country_code,
                'region': region,
                'postalCode': postal_code,
                'addressLine1': address_line_1
            }
        }).execute()

        # Mark the domain for deletion in approx 5 days.
        taskqueue.add(url="/tasks/cleanup",
                      countdown=settings.DOMAIN_CLEANUP_TIMER,
                      params={
                          'domain': domain
                      })

        return method


class StepTwoHandler(ApiHandler):

    @csrf_protect
    def post(self):

        domain = self.json_data['domain']
        numberOfSeats = self.json_data['numberOfSeats']

        service = build(serviceName="reseller",
                        version=settings.RESELLER_API_VERSION,
                        http=get_authorized_http())

        response = service.subscriptions().insert(
            customerId=domain,
            body={
                'customerId': domain,
                'subscriptionId': "%s-apps" % domain,
                'skuId': ResellerSKU.GoogleApps,
                'plan': {
                    'planName': ResellerPlanName.Flexible,
                },
                'seats': {
                    'numberOfSeats': numberOfSeats,
                    'maximumNumberOfSeats': numberOfSeats
                },
                'renewalSettings': {
                    'renewalType': ResellerRenewalType.PayAsYouGo
                },
                'purchaseOrderId': 'G00gl39001'
            }).execute(num_retries=5)

        return response


class StepThreeHandler(ApiHandler):

    @csrf_protect
    def post(self):
        '''
        Call the site verification api and fetch the token value.
        '''

        # establish default values.
        verification_type = self.json_data['verificationType']
        identifier = self.json_data['verificationIdentifier']
        verification_method = self.json_data['verificationMethod']

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

        return {
            'verification_token': response['token'],
            'verification_type': verification_type,
            'verification_method': verification_method,
            'verification_identifier': identifier
        }


class StepFourHandler(ApiHandler):

    @csrf_protect
    def post(self):
        """
        Call site verification service with token.

        Call the site verification service and see if the
        token has been fulfilled (e.g. a dns entry added)
        """

        service = build(serviceName="siteVerification",
                        version="v1",
                        http=get_authorized_http())

        verification_type = self.json_data.get("verification_type")
        verification_ident = self.json_data.get("verification_identifier")
        verification_method = self.json_data.get("verification_method")

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


class StepFiveHandler(ApiHandler):

    @csrf_protect
    def post(self):
        domain = self.json_data['domain']
        username = "admin@%s" % domain
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

        return {
            'domain': domain,
            'username': username,
            'password': password
        }


class StepSixHandler(ApiHandler):

    @csrf_protect
    def post(self):
        domain = self.json_data['domain']

        service = build(serviceName="reseller",
                        version=settings.RESELLER_API_VERSION,
                        http=get_authorized_http())

        response = service.subscriptions().insert(
            customerId=domain,
            body={
                'customerId': domain,
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

        return response


class StepSevenHandler(ApiHandler):

    @csrf_protect
    def post(self):
        domain = self.json_data['domain']

        service = build(serviceName="licensing",
                        version='v1',
                        http=get_authorized_http())

        service.licenseAssignments().insert(
            productId=ResellerProduct.GoogleDrive,
            skuId=ResellerSKU.GoogleDriveStorage20GB,
            body={
                'userId': 'admin@%s' % domain
            }).execute(num_retries=5)


app = WSGIApplication(routes=[

    # Reseller Provisioning Flow API Methods
    (r'/api/createCustomer', StepOneHandler),
    (r'/api/createSubscription', StepTwoHandler),
    (r'/api/getSiteValidationToken', StepThreeHandler),
    (r'/api/testValidation', StepFourHandler),
    (r'/api/createUser', StepFiveHandler),
    (r'/api/createDriveStorageSubscription', StepSixHandler),
    (r'/api/assignDriveLicense', StepSevenHandler),

    # Generic Template Method.
    (r'/.*', IndexHandler)
], config=settings.WEBAPP2_CONFIG)
