// This emails a list of users that have enabled IMAP to
// the configured email address.
//
//**********************************************************************
//*                      LICENSING AND DISCLAIMER                      *
//**********************************************************************
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
//   DISCLAIMER:
//
//   (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS"
//   WITHOUT ANY WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR
//   OTHERWISE, INCLUDING, WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF
//   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-
//   INFRINGEMENT; AND
//
//   (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES,
//   PROFIT OR DATA, OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL,
//   INCIDENTAL OR PUNITIVE DAMAGES, HOWEVER CAUSED AND REGARDLESS OF
//   THE THEORY OF LIABILITY, EVEN IF GOOGLE HAS BEEN ADVISED OF THE
//   POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF THE USE OR INABILITY
//   TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR ITS
//   DERIVATIVES.

function reportImapEnabledUsers() {

  var report_recipient_email_address = 'admin@example.com';

  var domain = UserManager.getDomain();
  var service_name = 'imap-audit';
  var base_url = 'https://apps-apis.google.com/a/feeds/emailsettings/2.0/';
  var api_scope = encodeURIComponent(base_url);
  var imap_enabled_users = new Array();

  var users = UserManager.getAllUsers();
  for (var i in users) {
    var url = base_url + domain + '/' + users[i].getUserLoginId() +
              '/imap?alt=json';
    var urlFetch = UrlFetchApp.fetch(url, _googleOAuth(service_name,
                                                       api_scope));
    var jsonString = urlFetch.getContentText();
    var imap_val = Utilities.jsonParse(jsonString).entry.apps$property[0].value;
    if (imap_val == "true") {
      imap_enabled_users.push(users[i].getUserLoginId());
    }
  }

  if (imap_enabled_users.length > 0) {
    MailApp.sendEmail(report_recipient_email_address,
                      "Users With IMAP Enabled",
                      "email body",
                      {htmlBody: _getEmailHtml(domain, imap_enabled_users)});
  }

  function _googleOAuth(service_name, scope) {
    var oAuthConfig = UrlFetchApp.addOAuthService(service_name);
    oAuthConfig.setRequestTokenUrl(
        "https://www.google.com/accounts/OAuthGetRequestToken?scope=" +
        scope);
    oAuthConfig.setAuthorizationUrl(
        "https://www.google.com/accounts/OAuthAuthorizeToken");
    oAuthConfig.setAccessTokenUrl(
        "https://www.google.com/accounts/OAuthGetAccessToken");
    oAuthConfig.setConsumerKey("anonymous");
    oAuthConfig.setConsumerSecret("anonymous");
    return {oAuthServiceName:service_name,
            oAuthUseToken:"always",
            method:"GET"};
  }

  function _getEmailHtml(domain, imap_enabled_users) {
    var email_html = "<html><head></head><body>";
    email_html += "<p>The following is a list of users in the domain " +
                  domain +
                  " that have enabled IMAP in their Gmail settings.</p>"
    email_html += "<table cellspacing='0' cellpadding='1'>";
    email_html += "  <tbody>";
    for (var i in imap_enabled_users) {
      email_html += "<tr><td>" + imap_enabled_users[i] + "</td></tr>";
    }
    email_html += "    </tbody>";
    email_html += "</table>";
    email_html += "</body></html>";
    return email_html;
  }
}
