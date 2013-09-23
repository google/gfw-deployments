// Applies Email Delegation based on delegate/delegator pairs
// provided in a Google Spreadsheet.
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
//**********************************************************************
//
// Usage:
//   - Create a tab in a Google Spreadsheet named "Delegation".
//   - Add the Delegator to Column A of the Google Spreadsheet
//   - Add the Delegate to Column B.
//   - Substitute the Spreadsheet key to the spreadsheet_key variable below.
//   - Substitute the domain in the domain variable below.
//   - Make sure Column C is empty (we write to it)
//   - Run the addDelegate script to apply the delegation for each row.
//
//  NOTE: This script currently assumes it is setting up delegation
//        for the first time for these users.  In its current form,
//        It does NOT check whether delegation has already been applied.
function addDelegate() {

  var spreadsheet_key = "YOURSPREADSHEETKEY";
  var domain = "example.com";
  var sheet_name = "Delegation";
  var service_name = "delegation-appsscript";
  var num_data_columns = 2;
  var spreadsheet = SpreadsheetApp.openById(spreadsheet_key);
  var sheet = spreadsheet.getSheetByName(sheet_name);
  var data_range = sheet.getDataRange();

  // Check that sheet has at least two columns
  if (data_range.getNumColumns() < num_data_columns) {
    Logger.log("Input Sheet has too few columns.  Exiting");
    return;
  }

  var values = data_range.getValues();
  for (var i=0; i < values.length; i++) {
    var delegator = values[i][0];
    var delegate = values[i][1];
    Logger.log("Applying email delegation for " + delegate +
               " to access " +  delegator + "'s mail");
    try {
      _delegateApiCall(service_name, domain, delegator,
                       delegate);
      sheet.getRange(i+1, 3, 1, 1)
             .setValue("Delegation applied")
             .setBackgroundColor("Green")
             .setFontColor("White");
    } catch (err) {
      Logger.log("ERROR: Operation failed giving delegation rights to " +
                 delegate + " to access " +  delegator + "'s mail:" +
                 err.message);
      sheet.getRange(i+1, 3, 1, 1)
             .setValue("Delegation failed")
             .setBackgroundColor("Red")
             .setFontColor("White");
    }
  }

  function _googleOAuth(service_name, api_scope, http_method, http_payload) {
    var oAuthConfig = UrlFetchApp.addOAuthService(service_name);
    var api_scope = encodeURIComponent(
        'https://apps-apis.google.com/a/feeds/emailsettings/2.0/');
    oAuthConfig.setRequestTokenUrl(
        'https://www.google.com/accounts/OAuthGetRequestToken?scope=' +
        api_scope);
    oAuthConfig.setAuthorizationUrl(
        'https://www.google.com/accounts/OAuthAuthorizeToken');
    oAuthConfig.setAccessTokenUrl(
        'https://www.google.com/accounts/OAuthGetAccessToken');
    oAuthConfig.setConsumerKey('anonymous');
    oAuthConfig.setConsumerSecret('anonymous');
    return {oAuthServiceName:service_name,
            oAuthUseToken:'always',
            method:http_method,
            contentType:"application/atom+xml",
            payload:http_payload};
  }

  function _delegateApiCall(service_name, domain, delegator, delegate) {
    var scope = 'https://apps-apis.google.com/a/feeds/emailsettings/2.0/';
    var url = scope + domain + "/" + delegator.split('@')[0] + "/delegation";

    // Build Atom Request
    var xmlBody = Xml.element("atom:entry",[
      Xml.attribute("xmlns:atom","http://www.w3.org/2005/Atom"),
      Xml.attribute("xmlns:apps", "http://schemas.google.com/apps/2006"),
        Xml.element("apps:property", [
          Xml.attribute("name", "address"),
          Xml.attribute("value", delegate)
        ])
      ]);
    var payload = Utilities.newBlob(xmlBody.toXmlString()).getBytes();
    var result = UrlFetchApp.fetch(url, _googleOAuth(service_name, scope,
                                                     "post", payload));
  }
}
