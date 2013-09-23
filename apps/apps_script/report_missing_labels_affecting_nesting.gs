////////////////////////////////////////////////////////////////////////////////
// This is a reference implementation of a script that scans a user's labels
// looking for missing labels that are affecting nesting
// The script prints the labels it thinks should be created 
// to the log via Logger.log.
//
// Example #1: If a user has the labels:
//   - A
//   - A/B/C
// this won't nest properly because A/B is missing.
// The function fixAllMissingLabels would catch this and the following example.
//
// Example #2: If a user has the labels:
//   - A/B/C
//   - A/B/D
//   - A/B
// this also won't nest properly because the label A is missing.
// The function fixTopLevelMissingLabels would catch this, but not the 
// previous example.
//
////////////////////////////////////////////////////////////////////////////////

// Username we are going to check labels for
USERNAME="mdauphinee@mdauphinee.info";

// This function just looks for missing top level labels
function fixTopLevelMissingLabels() {
  _labelManager("top_only");
}

// This function looks for missing labels at any level
function fixAllMissingLabels() {
  _labelManager("all");
}

// Do not call this function directly.
// Rather use fixTopLevelMissingLabels or fixAllMissingLabels
function _labelManager(mode) {
  
  //var USERNAME = Browser.inputBox("Enter account name (full email address)");
  var labels_to_create = new Object();
  
  var result = _getXml(USERNAME);
  var label_list = _getLabelList(result);
  
  for (var l in label_list) {
    if (_isNestedLabel(label_list[l])) {
      if (mode == "all") { 
        var all_possible_parents = _getPossibleParents(label_list[l]);
        for (var p in all_possible_parents) {
          if (label_list.indexOf(all_possible_parents[p]) == -1) {
            labels_to_create[all_possible_parents[p]] = 1;
          }
        }
      } else if (mode == "top_only") { 
        var top_parent = label_list[l].split('/')[0];
        if (label_list.indexOf(top_parent) == -1) {
          labels_to_create[top_parent] = 1;
        }
      }
    }
  }
  
  // Report the deduplicated list of labels to create
  for (var element in labels_to_create) {
    Logger.log('Label [' + element + '] is missing');
  }
  
  // This creates an array of all the possible labels
  // given a label with slashes
  function _getPossibleParents(label_name) {
    var possible_labels = [];
    var label_string = "";
    var actual_levels = label_name.split('/');
    for (var l in actual_levels) {
      label_string += actual_levels[l]
      //Logger.log("Possible " + label_string);
      possible_labels.push(label_string);
      label_string += "/";
    }
    return possible_labels;
  }
  
  // Determines whether this label should be nested
  function _isNestedLabel(label_name) {
    return label_list[l].split('/').length > 1;
  }
  
  function _getXml(user_name) {
    var service_name = "label-manager";
    var scope = 'https://apps-apis.google.com/a/feeds/emailsettings/2.0/';
    var oAuthConfig = UrlFetchApp.addOAuthService(service_name);
  
    oAuthConfig.setRequestTokenUrl("https://www.google.com/accounts/OAuthGetRequestToken?scope=" + scope);
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
  
    var scope = 'https://apps-apis.google.com/a/feeds/emailsettings/2.0/';
    var url = scope + user_name.split('@')[1] + "/" + user_name.split('@')[0] + "/label";
 
    var result = UrlFetchApp.fetch(url, requestData); 
    return result;
  }
  
  function _getLabelList(result) {
    var label_list = [];
    var resultString = result.getContentText();
    var xml_doc = Xml.parse(resultString, true);
    var labels = xml_doc.feed.entry;
    for( var o in labels ) {
      for(var i in labels[o].getElements("property")) {
        if (labels[o].getElements("property")[i].name == "label") {
          //Logger.log(labels[o].getElements("property")[i].value);
          label_list.push(labels[o].getElements("property")[i].value);
        }
      }
    }
    
    return label_list;
  }
}
