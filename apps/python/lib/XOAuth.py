#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.
"""
XOAuth.py is a library used for authentication and authorization via XOAuth

Inputs:
  key:    An OAuth key
  secret: An OAuth secret

Usage:
  import imaplib
  from XOAuth import XOAuth

  xoauth = XOAuth(key, secret)
  xoauth_string = xoauth.GetXOAuthString(email_address, 'GET', 'imap')
  imap_conenction = imaplib.IMAP4_SSL(imap_server, imap_port)
  imap_connection.authenticate('XOAUTH', lambda x: xoauth_string)


Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

###########################################################################
DISCLAIMER:

(i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND

(ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR ITS
DERIVATIVES.
###########################################################################
"""

import base64
import hashlib
import hmac
import random
import time
import urllib

class XOAuth(object):
  """A wrapper of functions and data required to establish an XOAuth token."""

  def __init__(self, key, secret):
    """
    Input:
      key:    An OAuth key
      secret: The OAuth secret
    """
    self.key = key
    self.secret = secret

  def _EscapeAndJoin(self, elems):
    return '&'.join([self._UrlEscape(x) for x in elems])

  def _FormatUrlParams(self, params):
    """Formats parameters into a URL query string.

    Args:
      params: A key-value map.

    Returns:
      A URL query string version of the given parameters.
    """
    param_fragments = []
    for param in sorted(params.iteritems(), key=lambda x: x[0]):
      param_fragments.append('%s=%s' % (param[0], self._UrlEscape(param[1])))

    return '&'.join(param_fragments)

  def _UrlEscape(self, text):
    # See OAUTH 5.1 for a definition of which characters need to be escaped.
    return urllib.quote(text, safe='~-._')

  def _GenerateOauthSignature(self, base_string, consumer_secret,
                              token_secret=''):
    key = self._EscapeAndJoin([consumer_secret, token_secret])

    return self._GenerateHmacSha1Signature(base_string, key)

  def _GenerateHmacSha1Signature(self, text, key):
    digest = hmac.new(key, text, hashlib.sha1)

    return base64.b64encode(digest.digest())

  def _GenerateSignatureBaseString(self, method, request_url_base, params):
    """Generates an OAuth signature base string.

    Args:
      method: The HTTP request method, e.g. "GET".
      request_url_base: The base of the requested URL. For example, if the
        requested URL is
        "https://mail.google.com/mail/b/xxx@domain.com/imap/?" +
        "xoauth_requestor_id=xxx@domain.com", the request_url_base would be
        "https://mail.google.com/mail/b/xxx@domain.com/imap/".
      params: Key-value map of OAuth parameters, plus any parameters from the
        request URL.

    Returns:
      A signature base string prepared according to the OAuth Spec.
    """
    return self._EscapeAndJoin([method, request_url_base,
                               self._FormatUrlParams(params)])

  def _FillInCommonOauthParams(self, params):
    """Fills in parameters that are common to all oauth requests.

    Args:
      params: Parameter map, which will be added to.
    """

    params['oauth_consumer_key'] = self.key
    params['oauth_nonce'] = str(random.randrange(2**64 - 1))
    params['oauth_signature_method'] = 'HMAC-SHA1'
    params['oauth_version'] = '1.0'
    params['oauth_timestamp'] = str(int(time.time()))

  def GetXOAuthString(self, xoauth_requestor_id, method, protocol):
    """Generates an IMAP XOAUTH authentication string.

    Args:
      xoauth_requestor_id: The Google Mail user who's inbox will be
                           searched (full email address)
      method: The HTTP method used in the API request
      protocol: The protocol used in the API request

    Returns:
      A string that can be passed as the argument to an IMAP
      "AUTHENTICATE XOAUTH" command after being base64-encoded.
    """
    url_params = {}
    url_params['xoauth_requestor_id'] = xoauth_requestor_id
    oauth_params = {}
    self._FillInCommonOauthParams(oauth_params)

    signed_params = oauth_params.copy()
    signed_params.update(url_params)
    request_url_base = ('https://mail.google.com/mail/b/%s/%s/' % (
                        xoauth_requestor_id, protocol))
    base_string = self._GenerateSignatureBaseString(method, request_url_base,
                                                    signed_params)

    oauth_params['oauth_signature'] = self._GenerateOauthSignature(base_string,
        self.secret)

    # Build list of oauth parameters
    formatted_params = []
    for k, v in sorted(oauth_params.iteritems()):
      formatted_params.append('%s="%s"' % (k, self._UrlEscape(v)))
    param_list = ','.join(formatted_params)

    # Append URL parameters to request url, if present
    if url_params:
      request_url = '%s?%s' % (request_url_base,
                               self._FormatUrlParams(url_params))
    else:
      request_url = request_url_base

    return '%s %s %s' % (method, request_url, param_list)
