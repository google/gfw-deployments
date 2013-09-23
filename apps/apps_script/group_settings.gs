// The following script will check for group settings for each group.
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
// - Substitute the desired application/service name to APP_NAME variable.
// - Substitute the spreadsheet key to the SPREADSHEET_KEY variable below.
// - Substitute the sheet name to the SHEET_NAME variable below.
// - Substitute the oauth client id to the CLIENT_ID variable below.
// - Substitute the oauth client secret to the CLIENT_SECRET variable below.
// - Substitute the estimated pagination size estimated by total count of
//   groups in domain devided by 100 rounded up. See the Provisioning API
//   reference below for details on Results Pagination.
//   https://developers.google.com/google-apps/provisioning/reference#
//
//GLOBAL VARIABLES

var DOMAIN = 'YOURDOMAIN';
var APP_NAME = 'Appscript-sample2';
var CLIENT_ID = 'YOUR_CLIENT_ID';
var CLIENT_SECRET = 'YOUR_CLIENT_SECRET';
var SPREADSHEET_KEY = 'YOUR_SPREADSHEET_KEY';
var SHEET_NAME = 'Groupsettings';
var PAGINATION_SIZE = 1;

function checkGroupSettings() {
  var api_scope = 'https://www.googleapis.com/auth/apps.groups.settings';
  var spreadsheet = SpreadsheetApp.openById(SPREADSHEET_KEY);
  var sheet = spreadsheet.getSheetByName(SHEET_NAME);
  var header = [['name', 'email', 'description', 'whoCanViewMembership',
                 'whoCanJoin', 'whoCanViewGroup', 'whoCanInvite',
                 'allowExternalMembers', 'whoCanPostMessage', 'allowWebPosting',
                 'isArchived', 'archiveOnly', 'showInGroupDirectory',
                 'membersCanPostAsTheGroup', 'messageModerationLevel',
                 'replyTo', 'customReplyTo', 'sendMessageDenyNotification',
                 'defaultMessageDenyNotificationText',
                 'allowGoogleCommunication', 'messageDisplayFont',
                 'maxMessageBytes', 'messageDisplayFont']];

  sheet.clear().clearContents().clearFormats();
  Utilities.sleep(500);
  sheet.getRange(1, 1, 1, 23).setValues(header).setBackgroundColor('Lightblue');
  sheet.getRange(1, 1, 1, 23).setFontWeight('Bold');

  try {
    var groups = _getAllGroups();
    groups.sort();
  } catch (err) {
     Logger.log('ERROR: UrlFetch failed to retrieve all groups in domain' +
                err.message);
  }

  for (var i = 0; i < groups.length; i++) {
    var url = 'https://www.googleapis.com/groups/v1/groups/' + groups[i];
    try {
      Utilities.sleep(500);
      var result = UrlFetchApp.fetch(url, _googleOauth(APP_NAME, api_scope));
      var result = result.getContentText();
    } catch (err) {
      Logger.log('ERROR: UrlFetch failed to get group settings feed for' +
                 groups[i] + '  ' + err.message);
    }

    var xml_doc = Xml.parse(result, true);
    var entry = Xml.parse(result, true).entry;

    var email = entry.email.getText();
    var name = entry.name.getText();
    var description = entry.description.getText();
    var whoCanViewMembership = entry.whoCanViewMembership.getText();
    var whoCanJoin = entry.whoCanJoin.getText();
    var whoCanViewGroup = entry.whoCanViewGroup.getText();
    var whoCanInvite = entry.whoCanInvite.getText();
    var allowExternalMembers = entry.allowExternalMembers.getText();
    var whoCanPostMessage = entry.whoCanPostMessage.getText();
    var allowWebPosting = entry.allowWebPosting.getText();
    var maxMessageBytes = entry.maxMessageBytes.getText();
    var isArchived = entry.isArchived.getText();
    var archiveOnly = entry.archiveOnly.getText();
    var messageModerationLevel = entry.messageModerationLevel.getText();
    var replyTo = entry.replyTo.getText();
    var customReplyTo = entry.customReplyTo.getText();
    var sendMessageDenyNotif = entry.sendMessageDenyNotification.getText();
    var messageDenyNotif = entry.defaultMessageDenyNotificationText.getText();
    var showInGroupDirectory = entry.showInGroupDirectory.getText();
    var allowGoogleCommunication = entry.allowGoogleCommunication.getText();
    var allowWebPosting = entry.allowWebPosting.getText();
    var membersCanPostAsTheGroup = entry.membersCanPostAsTheGroup.getText();
    var messageDisplayFont = entry.messageDisplayFont.getText();

    var settings = [[name, email, description, whoCanViewMembership,
                 whoCanJoin, whoCanViewGroup, whoCanInvite,
                 allowExternalMembers, whoCanPostMessage, allowWebPosting,
                 isArchived, archiveOnly, showInGroupDirectory,
                 membersCanPostAsTheGroup, messageModerationLevel, replyTo,
                 customReplyTo, sendMessageDenyNotif, messageDenyNotif,
                 allowGoogleCommunication, messageDisplayFont,
                 maxMessageBytes, messageDisplayFont]];

    sheet.getRange(i + 2, 1, 1, 23).setValues(settings);
  }

  function _getAllGroups() {
    var api_scope = 'https://apps-apis.google.com/a/feeds/groups/';
    var args = _googleOauth(APP_NAME, api_scope);
    var nextUrl = '';
    var all_groups = [];

    for (var x = 1; x <= PAGINATION_SIZE; x++) {
      var xml_doc = _getXmlFeed(nextUrl);
      var groups_array = _getAppsProperty(xml_doc, 'groupId');
      for (var g = 0; g < groups_array.length; g++) {
        all_groups.push(groups_array[g]);
      }

      var feed_Links = xml_doc.feed.link;
      var g = [];
      for (var j in feed_Links) {
        if ([feed_Links[j].rel] == 'next') {
          g.push([feed_Links[j].href]);
        }
      }
      nextUrl = g;

    }
    return all_groups;

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

  function _getXmlFeed(urlNext) {
    var api_scope = 'https://apps-apis.google.com/a/feeds/groups/';
    var fetchArgs = _googleOauth('apps_test', api_scope);
    if (urlNext != '') {
      var url = urlNext;
      Logger.log(url);
    } else {
     var url = 'https://apps-apis.google.com/a/feeds/group/2.0/' + DOMAIN;
    }

  var result = UrlFetchApp.fetch(url, fetchArgs).getContentText();
  var xml_doc = Xml.parse(result, true);

  return xml_doc;
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

    if (api_scope == 'https://www.googleapis.com/auth/apps.groups.settings') {
      oAuthConfig.setConsumerKey(CLIENT_ID);
      oAuthConfig.setConsumerSecret(CLIENT_SECRET);
    } else {
      oAuthConfig.setConsumerKey('anonymous');
      oAuthConfig.setConsumerSecret('anonymous');
    }

    var requestData = {
      'method': 'GET',
      'oAuthServiceName': APP_NAME,
      'headers': { 'GData-Version': '2.0' },
      'oAuthUseToken': 'always'
    };

    return requestData;
  }

}