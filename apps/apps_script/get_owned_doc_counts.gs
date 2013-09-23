// Counts the number of Google Documents owned by the users
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
//   - Create a tab in a Google Spreadsheet named "Document Counts".
//   - Add email addresses to Column A for those users we will count documents
//   - Substitute the Spreadsheet key to the spreadsheet_key variable below.
//   - Substitute the domain in the domain variable below.
//   - Make sure Column B is empty (we write to it)
//   - Run the getDocCount script to apply the delegation for each row.
//
//  NOTE: Folders of Collections are not included in the total.
function getOwnedDocumentCount() {

  var spreadsheet_key = "YOURSPREADSHEETKEY";
  var domain = "example.com";
  var sheet_name = "Document Counts";
  var service_name = "doc-count-appsscript";
  var num_data_columns = 1;
  var spreadsheet = SpreadsheetApp.openById(spreadsheet_key);
  var sheet = spreadsheet.getSheetByName(sheet_name);
  var data_range = sheet.getDataRange();

  var values = data_range.getValues();
  for (var i=0; i < values.length; i++) {
    var user_email_address = values[i][0];
    Logger.log("Getting document count for " + user_email_address);
    try {
      var num_docs = _getOwnedDocsCount(user_email_address, service_name);
      sheet.getRange(i+1, 2, 1, 1)
             .setValue(num_docs)
             .setBackgroundColor("Green")
             .setFontColor("White");
    } catch (err) {
      Logger.log('ERROR: Counting document operation failed for ' +
                 user_email_address + ":" + err.message);
      sheet.getRange(i+1, 2, 1, 1)
             .setValue("Count operation failed")
             .setBackgroundColor("Red")
             .setFontColor("White");
    }
  }

  function _getOwnedDocsCount(email_address, service_name) {
    var scope = 'https://docs.google.com/feeds/';
    var url = 'https://docs.google.com/feeds/' + email_address +
              '/private/full/?owner=' + encodeURIComponent(email_address);
    var result = UrlFetchApp.fetch(url, _docsGoogleOAuth(service_name,
                                                         scope,
                                                         "get",
                                                         null));
    var docs_xml_document = Xml.parse(result.getContentText(), true);
    var root = docs_xml_document.getElement(); // feed element
    var entries = root.getElements("entry");
    return entries.length;
  }

  function _docsGoogleOAuth(service_name, api_scope, http_method, http_payload) {
    var oAuthConfig = UrlFetchApp.addOAuthService(service_name);
    var api_scope = encodeURIComponent('https://docs.google.com/feeds/');
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
            headers : {"GData-Version": "3.0"},
            method:http_method,
            contentType:"application/atom+xml",
            payload:http_payload};
  }
}
