// The following script will check whether a non-primary domain nickname
// used for mail forward purposes has been created for each user in a specified
// domain. For example, it may be desired for all users in nonprimary.domain.com
// have a nickname as username@galias.com so that mail sent to a legacy mail
// system could be forwarded to. Currently NicknameManager and UserManager does
// not support multi-domain, so UrlFetchApp is used to access multi-domain user
// accounts and nicknames.
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
//
// - Substitute the domain name to the DOMAIN variable.
// - Substitute the domain name used for forwarding to the DOMAIN_FOR_FORWARDING
//   variable.
// - Substitute the desired application/service name to APP_NAME variable.
// - Substitute the spreadsheet key to the SPREADSHEET_KEY variable below.
// - Substitute the sheet name to the SHEET_NAME variable below.
// - Substitute the estimated pagination size estimated by total number of users in
//   the domain divided by 100 rounded up. See the Provisioning API reference
//   below for details on Results Pagination.
//   https://developers.google.com/google-apps/provisioning/reference#

//GLOBAL VARIABLES

var DOMAIN = 'example.com';
var DOMAIN_FOR_FORWARDING = 'gtest.example.com';
var APP_NAME = 'Appscript-sample';
var SPREADSHEET_KEY = 'YOURSPREADSHEETKEY';
var SHEET_NAME = 'Aliases';
var PAGINATION_SIZE = 1;

function checkNicknames() {
  var spreadsheet = SpreadsheetApp.openById(SPREADSHEET_KEY);
  var sheet = spreadsheet.getSheetByName(SHEET_NAME);
  var userArray = _getAllUsers();
  var user_aliases = _getUserNicknames(userArray);
  var header = [['Email', 'Alias', 'Notes']];

  sheet.clear().clearContents().clearFormats();
  sheet.getRange(1, 1, 1, 3).setValues(header).setBackgroundColor('Lightblue');
  sheet.getRange(1, 1, 1, 3).setFontWeight('Bold');

  for (var i = 0; i < user_aliases.length; i++) {
    if (user_aliases[i][1] == 'NO_ALIAS_IN_FORWARDING_DOMAIN') {
      sheet.getRange(i + 2, 1, 1, 3).setValues([user_aliases[i]]);
      sheet.getRange(i + 2, 1, 1, 3).setBackground('Red');
    } else {
      sheet.getRange(i + 2, 1, 1, 3).setValues([user_aliases[i]]);
    }

  }

  function _getUserNicknames(userArray) {
    var api_scope = 'https://apps-apis.google.com/a/feeds/user/';
    var user_aliases = [];
    var APP_NAME = 'app_script_nicknames';
    var args = _googleOauth(APP_NAME, api_scope);

    for (i = 0; i < userArray.length; i++) {
      var url = 'https://apps-apis.google.com/a/feeds/alias/2.0/' + DOMAIN +
      '?userEmail=' + userArray[i];
      var result = UrlFetchApp.fetch(url, _googleOauth(APP_NAME, api_scope));
      var xml_doc = Xml.parse(result.getContentText(), true);
      var aliasesArray = _getAppsProperty(xml_doc, 'aliasEmail');
      if (aliasesArray.length > 0) {
        for (j = 0; j < aliasesArray.length; aliasesArray++) {
          if (aliasesArray[j].indexOf(DOMAIN_FOR_FORWARDING) != -1) {
            if (aliasesArray[j].split('@')[0] == userArray[i].split('@')[0]) {
                user_aliases.push([userArray[i], aliasesArray[j], 'match']);
            } else {
              user_aliases.push([userArray[i], aliasesArray[j],
                               'does not match login username']);
            }
          } else {
            user_aliases.push([userArray[i],
                             'NO_ALIAS_IN_FORWARDING_DOMAIN', '']);
          }
        }
      } else {
        user_aliases.push([userArray[i], 'NO_ALIAS_IN_FORWARDING_DOMAIN', '']);
      }

    }

    return user_aliases;

  }

  function _getAllUsers() {
    var user_array = [];
    var api_scope = 'https://apps-apis.google.com/a/feeds/user/';
    var args = _googleOauth(APP_NAME, api_scope);
    var x = 1;
    var nextUrl = '';

    for (x; x <= PAGINATION_SIZE; x++) {
      var xml = _getXmlFeed(nextUrl);
      var users_xml = xml.feed.entry;
      for (var j in users_xml) {
        user_array.push(users_xml[j].login.userName + '@' + DOMAIN);
      }
      var feed_Links = xml.feed.link;
      var g = [];
      for (var j in feed_Links) {
        if ([feed_Links[j].rel] == 'next') {
          g.push([feed_Links[j].href]);
        }
      }
      nextUrl = g;
    }

    return user_array;

  }

  function _getXmlFeed(urlNext) {
    var base = 'https://apps-apis.google.com/a/feeds/';
    var fetchArgs = _googleOauth('apps_test', base);
    if (urlNext != '') {
      var url = urlNext;
      Logger.log(url);
    } else {
     var url = base + DOMAIN + '/user/2.0';
    }

  var result = UrlFetchApp.fetch(url, fetchArgs).getContentText();
  var xml = Xml.parse(result);

  return xml;
  }

  function _getAppsProperty(xml_doc, attribute_name) {
    var results = new Array();
    var elements = xml_doc.getElement().getElements('entry');

    for (var i = 0; i < elements.length; i++) {
      var entry_element_prop = elements[i].getElements('property');
      for (var j = 0; j < entry_element_prop.length; j++) {
        var attributes = entry_element_prop[j].getAttributes();
        if (attributes[0].getValue() == attribute_name) {
            results.push(attributes[1].getValue());
        }
      }
    }

   return results;
  }

  function _googleOauth(APP_NAME, api_scope) {
    var oAuthConfig = UrlFetchApp.addOAuthService(APP_NAME);
    var url = 'https://www.google.com/accounts/OAuthGetRequestToken?scope=' +
               api_scope;
    var authorize_url = 'https://www.google.com/accounts/OAuthAuthorizeToken';
    var acctoken_url = 'https://www.google.com/accounts/OAuthGetAccessToken';

    oAuthConfig.setRequestTokenUrl(url);
    oAuthConfig.setAuthorizationUrl(authorize_url);
    oAuthConfig.setAccessTokenUrl(acctoken_url);
    oAuthConfig.setConsumerKey('anonymous');
    oAuthConfig.setConsumerSecret('anonymous');

    var requestData = {
      'method': 'GET',
      'oAuthServiceName': APP_NAME,
      'headers': { 'GData-Version': '2.0' },
      'oAuthUseToken': 'always'
    };

    return requestData;
  }

}
