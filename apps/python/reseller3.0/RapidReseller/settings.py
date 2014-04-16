#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.

__author__ = 'richieforeman@google.com (Richie Foreman)'

import os

ROOT = os.path.dirname(os.path.realpath(__file__))

# setup an API Console account, and provide this information.
OAUTH2_CLIENT_ID = ""
OAUTH2_SERVICE_ACCOUNT_EMAIL = ""

# a P12 private key provided by Google is used to sign requests.
# for use in Python on Google App Engine, the key must be in PEM format.
# openssl pkcs12 -in xxxxx.p12 -nodes -nocerts > privatekey.pem
OAUTH2_PRIVATEKEY = ROOT + "/privatekey.pem"

# Scopes declare what rights this application has access to.
OAUTH2_SCOPES = [
  'https://www.googleapis.com/auth/apps.order',
  'https://www.googleapis.com/auth/siteverification',
  'https://www.googleapis.com/auth/admin.directory.user',
  'https://www.googleapis.com/auth/apps.licensing'
]
RESELLER_DOMAIN = ""
RESELLER_ADMIN = ""
RESELLER_API_VERSION = 'v1'

SESSION_MAX_AGE = 86400
SESSION_BACKEND = "memcache"

WEBAPP2_CONFIG = {
  'webapp2_extras.sessions': {
    'secret_key': 'webapp2requiresthis'
  }
}

SITE_VERIFICATION_METHODS = ['FILE', 'META', 'ANALYTICS', 'TAG_MANAGER']
INET_DOMAIN_VERIFICATION_METHODS = ['DNS_TXT', 'DNS_CNAME']

DOMAIN_TEMPLATE = "demo-%d.acmecorp.com"

# clean up domains after 2 days.
DOMAIN_CLEANUP_TIMER = (86400 * 2)

try:
  # utilize a local settings file.
  from settings_local import *
except ImportError:
  # running on prod/public.
  pass
