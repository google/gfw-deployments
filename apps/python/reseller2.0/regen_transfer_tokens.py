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
    Provides the ability to export resold customers and a transfer token
    valid for up to 5 days using the Reseller 2.0 API.

    This API is built upon the older GData system, and a lightweight wrapper
    has been implemented.

    Setup:
    - Download and install the Python GData libraries
      (https://code.google.com/p/gdata-python-client/)

    Usage:
    - python export-reseller2-customers.py --admin admin@reseller.acmecorp.com
      --password <password> --domain reseller.acmecorp.com --out mycustomers.csv
"""

from argparse import ArgumentParser
import csv
import random
import time

import atom
import gdata.client
import gdata.data
import gdata.gauth

from gdata.apps.multidomain.client import MultiDomainProvisioningClient
from gdata.client import RequestError

DOMAIN_FEED_TEMPLATE = "/a/feeds/reseller/%s/%s/domain"
TRANSFER_TOKEN_TEMPLATE = "/a/feeds/reseller/%s/%s/domain/%s/transferToken"
DOMAIN_ENTRY_TEMPLATE = "/a/feeds/reseller/%s/%s/domain/%s"
SUSPEND_ENTRY_TEMPALTE = "/a/feeds/reseller/%s/%s/domain/%s/suspend"

class Reseller2Client(gdata.client.GDClient):
    host = "apps-apis.google.com"
    api_version = "2.0"
    ssl = True
    auth_service = "apps"
    domain = None

    def __init__(self, domain, auth_token=None, **kwargs):
        gdata.client.GDClient.__init__(self,
                                       auth_token=auth_token,
                                       **kwargs)
        self.domain = domain

    def get_all_domains(self):
        '''
        A generator that transparently pages through
        a gdata feed of domains and yields each entry.
        '''
        print "Fetching page of domains... "

        domain_uri = DOMAIN_FEED_TEMPLATE % (self.api_version,
                                     self.domain)

        while domain_uri is not None:
            feed = self.get_entry(uri=domain_uri,
                                  desired_class=gdata.data.GDFeed)

            for e in feed.entry:
                yield e

            # keep the QPS something reasonable.
            time.sleep(1)

            if feed.GetNextLink():
                domain_uri = feed.GetNextLink().href
            else:
                domain_uri = None

    def get_domain(self, domain):
        domain_uri = DOMAIN_ENTRY_TEMPLATE % (self.api_version,
                                              self.domain,
                                              domain)

        return self.get_entry(uri=domain_uri, desired_class=gdata.data.GDEntry)

    def list_domains(self, startDomainName=''):
        '''
        A simple single page list call.
        '''
        domain_uri = DOMAIN_FEED_TEMPLATE % (self.api_version,
                                             self.domain)

        domain_uri = atom.http_core.Uri.parse_uri(domain_uri)
        domain_uri.query['startDomainName'] = startDomainName

        return self.get_entry(uri=domain_uri,
                              desired_class=gdata.data.GDFeed)

    def get_suspend_status(self, domain):
        suspend_uri = SUSPEND_ENTRY_TEMPALTE % (self.api_version,
                                                self.domain,
                                                domain)

        return self.get_entry(uri=suspend_uri,
                              desired_class=gdata.data.GDEntry)

    def get_transfer_token(self, domain):
        '''
        Given a reseller domain, fetch the transfer token.
        '''
        token_uri = TRANSFER_TOKEN_TEMPLATE % (self.api_version,
                                               self.domain,
                                               domain)
        return self.get_entry(uri=token_uri,
                              desired_class=gdata.data.GDEntry)

def main(args):
    client = Reseller2Client(domain=args.domain)

    auth_token = client.client_login(email=args.admin,
                                     password=args.password,
                                     source="edt-reseller2.0-tokendump")


    reader = csv.DictReader(open(args.in_file, 'r'))


    writer = csv.DictWriter(open(args.out, 'wb'),
                            fieldnames=[
                                'customerDomain',
                                'customerAuthToken',
                                'customer.customerId',
                                'customer.alternateEmail',
                                'customer.phoneNumber',
                                'customer.contactName',
                                'customer.organizationName',
                                'customer.locality',
                                'customer.region',
                                'customer.postalCode',
                                'customer.countryCode',
                                'customer.addressLine1',
                                'customer.addressLine2',
                                'customer.addressLine3',
                                'purchaseOrderId',
                                'skuId',
                                'plan.planName',
                                'renewalSettings.renewalType',
                                'seats.numberOfSeats',
                                'seats.maximumNumberOfSeats'
                            ])
    writer.writeheader()

    for r in reader:
      if r['customerDomain'] != "home.jazztel.es":
        continue

      print "Refreshing transfer token for domain: %s" % r['customerDomain']
      try:
        token_entry = client.get_transfer_token(r['customerDomain'])

        # pull out the values of interest.
        expiry = token_entry._other_elements[1]._other_attributes['value']
        token = token_entry._other_elements[2]._other_attributes['value']

        r['customerAuthToken'] = token
      except:
        r['customerAuthToken'] = "---ERROR---"

      writer.writerow(r)

if __name__ == "__main__":
    args = ArgumentParser()

    args.add_argument("--admin",
                      help="Administrative user on the reseller domain")
    args.add_argument("--password",
                      help="Password for the administrative user")
    args.add_argument("--domain",
                      help="Reseller domain (e.g. 'reseller.acmecorp.com')")
    args.add_argument("--in_file")
    args.add_argument("--out",
                      help="Output file for report (e.g. 'out.csv')")

    main(args.parse_args())