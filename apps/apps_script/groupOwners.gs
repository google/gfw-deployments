// The following script will record all groups in a domain, group owners,
// and specificy whether the group is user created.
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
//   - Substitute the spreadsheet key to the SPREADSHEET_KEY variable below.
//   - Substitute the sheet name to the SHEET_NAME variable below.
//   - Substitute the domain name to the DOMAIN variable below.

//GLOBAL VARIABLES
var DOMAIN = "example.com";
var SPREADSHEET_KEY = "YOURSPREADSHEETKEY";
var SHEET_NAME = "Groups";

function groupsReport(){
  var service_name = "app-script-test";
  var api_scope = "https://apps-apis.google.com/a/feeds/groups/";

  var groups_result =  _getGroups();
  if (groups_result)
   {
    var all_groups = groups_result[0];
    var non_usermgr_groups = groups_result[1];
   }
  else { return}

  var groups_list = new Array();
  var spreadsheet = SpreadsheetApp.openById(SPREADSHEET_KEY);
  var sheet = spreadsheet.getSheetByName(SHEET_NAME);
  var data_range = sheet.getDataRange();
  var values = data_range.getValues();

  for(g=0; g <all_groups.length; g++) {
    if (non_usermgr_groups.indexOf(all_groups[g]) != -1) {
        var grp_owners = _getGroupOwnersApi( all_groups[g], service_name);
        if(grp_owners) {
        groups_list.push([all_groups[g], grp_owners, "user_created"]);
        }
        else { groups_list.push([all_groups[g], " ", "user_managed"]) }
     }
    else { //Process admin created groups
       var grp_owners = _getGroupOwnersApi( all_groups[g], service_name);
       if(grp_owners){
         groups_list.push([all_groups[g], grp_owners, ""]);
       }
        else { groups_list.push([all_groups[g], " ", " "])}

     }
  }

  sheet.clear();
  var header = [["groupId", "owners", "notes"]]
  sheet.getRange(1,1, 1, 3).setValues(header);
  for (var i=1; i < groups_list.length; i++) {
       sheet.getRange(i+1,1, 1, 3).setValues([groups_list[i]]);

   };

}

//GroupsApp.Role.OWNER via Group Service is not used due to certain 
//restrictions on who can view group members. Provisioning API run by
//Super Admin can retrieve all group members regardless of Group Settings
// access restrictions

function _getGroupOwnersApi(groupId, service_name, api_scope) {
  var url = "https://apps-apis.google.com/a/feeds/group/2.0/" + DOMAIN + "/" + groupId + "/owner";
  var result = UrlFetchApp.fetch(url, _googleOauth(service_name, api_scope));
  var xml_doc = Xml.parse(result.getContentText(), true);
  var group_owners = _getAppsProperty(xml_doc, "email");

  return group_owners.toString();

} //end of function

function _getAppsProperty(xml_doc, attribute_name) {
  var results = new Array();
  var elements = xml_doc.getElement().getElements('entry');

  for(var i=0; i< elements.length; i++) {
      var entry_element_prop =  elements[i].getElements("property");
      for(var j=0; j < entry_element_prop.length; j++){
          var attributes = entry_element_prop[j].getAttributes();
          if (attributes[0].getValue() == attribute_name) {
              results.push(attributes[1].getValue());
            }
       }
   }

  return results;

}

function _getGroups(){
  var all_groups = new Array();
  var non_usermanaged_groups = new Array();
  var service_name = "app-script-test";
  var api_scope = "https://apps-apis.google.com/a/feeds/groups/";

  try {
    var result = UrlFetchApp.fetch("https://apps-apis.google.com/a/feeds/group/2.0/" +
    DOMAIN , _googleOauth(service_name, api_scope));
    var xml_doc = Xml.parse(result.getContentText(), true);
    var all_groups = _getAppsProperty(xml_doc, "groupId");

  } catch (err) {
    Logger.log("ERROR: UrlFetch failed to get all groups feed" + err.message);
    return

  }

  try {
    var result = UrlFetchApp.fetch("https://apps-apis.google.com/a/feeds/group/2.0/" +
                 DOMAIN + "?skipUserCreatedGroups=true", _googleOauth(service_name, api_scope));
    var resultString = result.getContentText();
    var xml_doc = Xml.parse(resultString, true);
    var non_usermgr_groups = _getAppsProperty(xml_doc, "groupId");
  }  catch (err) {
     Logger.log("ERROR: UrlFetch failed to get non user created groups feed" + err.message);
     return;

  }

  return [all_groups, non_usermgr_groups];
}


function _googleOauth(service_name, api_scope) {
  var oAuthConfig = UrlFetchApp.addOAuthService(service_name);
  oAuthConfig.setRequestTokenUrl("https://www.google.com/accounts/OAuthGetRequestToken?scope=" + api_scope);
  oAuthConfig.setAuthorizationUrl("https://www.google.com/accounts/OAuthAuthorizeToken");
  oAuthConfig.setAccessTokenUrl("https://www.google.com/accounts/OAuthGetAccessToken");
  oAuthConfig.setConsumerKey("anonymous");
  oAuthConfig.setConsumerSecret("anonymous");

  var requestData = {
    "method": "GET",
    "oAuthServiceName": service_name,
    "headers": { "GData-Version": "2.0" },
    "oAuthUseToken": "always"
    };

   return requestData;
}

