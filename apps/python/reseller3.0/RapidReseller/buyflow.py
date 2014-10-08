from apiclient.discovery import build
from apiclient.http import HttpError
from google.appengine.api import taskqueue

from app import ApiHandler

import settings

from utils import get_authorized_http
from utils import csrf_protect

class CreateCustomerHandler(ApiHandler):
  def _mark_domain_for_deletion(self, domain, countdown=settings.DOMAIN_CLEANUP_TIMER):
    taskqueue.add(url="/tasks/cleanup",
                  countdown=countdown,
                  params={
                    'domain': domain
                  })

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
    address_line_2 = self.json_data['postalAddress.addressLine2']

    service = build(serviceName="reseller",
                    version=settings.RESELLER_API_VERSION,
                    http=get_authorized_http())

    # test to see if the customer exists already.
    try:
      method = service.customers().get(
        customerId=domain).execute(num_retries=5)

      # call was successful, meaning the customer already exists, throw exception.
      raise Exception("That customer already exists")
    except HttpError, e:
      if int(e.resp['status']) == 404:
        pass
      else:
        # possible 500 error?
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
        'addressLine1': address_line_1,
        'addressLine2': address_line_2
      }
    }).execute(num_retries=5)

    # Mark the domain for deletion in approx 5 days.
    self._mark_domain_for_deletion(domain)

    return method


class CreateSubscriptionHandler(ApiHandler):

  @csrf_protect
  def post(self):
    domain = self.json_data['domain']
    numberOfSeats = self.json_data['numberOfSeats']
    skuId = self.json_data['skuId']
    planName = self.json_data['planName']
    renewalType = self.json_data['renewalType']
    purchaseOrderId = self.json_data['purchaseOrderId']
    
    service = build(serviceName="reseller",
                    version=settings.RESELLER_API_VERSION,
                    http=get_authorized_http())

    response = service.subscriptions().insert(
      customerId=domain,
      body={
        'customerId': domain,
        'skuId': skuId,
        'plan': {
          'planName': planName,
        },
        'seats': {
          'numberOfSeats': numberOfSeats,
          'maximumNumberOfSeats': numberOfSeats
        },
        'renewalSettings': {
          'renewalType': renewalType
        },
        'purchaseOrderId': purchaseOrderId
      }).execute(num_retries=5)

    return response


class GetSiteVerificationTokenHandler(ApiHandler):
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
      'verificationToken': response['token'],
      'verificationType': verification_type,
      'verificationMethod': verification_method,
      'verificationIdentifier': identifier
    }


class VerifySiteHandler(ApiHandler):
  @csrf_protect
  def post(self):
    """
    Call site verification service with token.

    Call the site verification service and see if the
    token has been fulfilled (e.g. a dns entry added)
    """

    verification_type = self.json_data.get("verificationType")
    verification_identifier = self.json_data.get("verificationIdentifier")
    verification_method = self.json_data.get("verificationMethod")

    service = build(serviceName="siteVerification",
                    version="v1",
                    http=get_authorized_http())

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


class CreateAdminUserHandler(ApiHandler):
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
