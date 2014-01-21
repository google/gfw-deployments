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

from google.appengine.api import memcache
import httplib2

import settings
from oauth2client.client import SignedJwtAssertionCredentials


def csrf_protect(func):
    def wrapper(instance):
        token = instance.request.get("token", None)

        if token is not None and token == instance.get_csrf_token():
            instance.regen_csrf_token()
            return func(instance)

        instance.abort(403)

    return wrapper


def get_authorized_http():
    credentials = get_credentials(sub=settings.RESELLER_ADMIN)

    http = httplib2.Http(timeout=20)
    credentials.authorize(http)
    return http


def get_credentials(sub=None):
    '''
    Signed JWT Credentials allow for frictionless authentication
    using a private key as opposed to a three-legged oauth flow.
    '''

    # fetch the credentials object from memcache.
    credentials = memcache.get("rapid-reseller#credentials#%s" % sub)

    if credentials is None or credentials.invalid:
        http = httplib2.Http()

        f = file(settings.OAUTH2_PRIVATEKEY)
        key = f.read()
        f.close()

        # establish the credentials.
        credentials = SignedJwtAssertionCredentials(
            service_account_name=settings.OAUTH2_SERVICE_ACCOUNT_EMAIL,
            private_key=key,
            scope=" ".join(settings.OAUTH2_SCOPES),
            sub=sub)

        # force the generation of an access token
        credentials.refresh(http)

        # cache the token for 59 minutes.
        memcache.set("rapid-reseller#credentials#%s" % sub,
                     value=credentials,
                     time=(60*59))

    return credentials