#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.

__author__ = 'richieforeman@google.com (Richie Foreman)'

from google.appengine.api import memcache
import httplib2
import logging

import settings
from oauth2client.client import SignedJwtAssertionCredentials


def csrf_protect(func):
    def wrapper(instance):
        if not instance.app._ENABLE_CSRF:
            return func(instance)

        # the token can come from a get param or a header.
        token_param = instance.request.get("token", None)
        token_header = instance.request.headers.get("X-Xsrf-Token", None)
        token = token_param or token_header

        if token is not None and token == instance.get_csrf_token():
            instance.regenerate_csrf_token()
            return func(instance)

        instance.abort(403)

    return wrapper


def get_authorized_http():
    credentials = get_credentials(sub=settings.RESELLER_ADMIN)
    http = httplib2.Http(timeout=20, cache=memcache.Client())
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
        logging.info("Couldn't find cached token, refreshing")

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
