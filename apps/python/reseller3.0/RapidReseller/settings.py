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

# setup an API Console account, and provide this information.
OAUTH2_CLIENT_ID = ""
OAUTH2_SERVICE_ACCOUNT_EMAIL = ""

# a P12 private key provided by Google is used to sign requests.
# for use in Python on Google App Engine, the key must be in PEM format.
# openssl pkcs12 -in xxxxx.p12 -nodes -nocerts > privatekey.pem
OAUTH2_PRIVATEKEY = "privatekey.pem"

# Scopes declare what rights this application has access to.
OAUTH2_SCOPES = [
    'https://www.googleapis.com/auth/apps.order',
    'https://www.googleapis.com/auth/siteverification',
    'https://apps-apis.google.com/a/feeds/user/',
    'https://www.googleapis.com/auth/admin.directory.user'
]

RESELLER_DOMAIN = ""
RESELLER_ADMIN = ""
RESELLER_API_VERSION = 'v1'

SESSION_MAXAGE = 86400
SESSION_BACKEND = "memcache"

WEBAPP2_CONFIG = {
    'webapp2_extras.sessions': {
        'secret_key': 'changeme'
    }
}

SITE_VERIFICATION_METHODS = ['FILE', 'META', 'ANALYTICS','TAG_MANAGER']
INET_DOMAIN_VERIFICATION_METHODS = ['DNS_TXT', 'DNS_CNAME']