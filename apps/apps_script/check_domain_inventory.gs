// The following script will read in a list of domains from
// a Google Spreadsheet and check whether the domain is a
// Team Edition domain, or secondarily whether it is provisioned or not.
//
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
//###########################################################################
// DISCLAIMER:
//
// (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
// WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
// WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
// PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND
//
// (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
// OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
// DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
// GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
// THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR ITS
// DERIVATIVES.
//###########################################################################
//
// Usage:
//   There are two ways to use this script:
//     1. As an application which checks all domains in column A, placing
//        their status in column B.
//     2. As a spreadsheet function called IsGAppsDomain() with the domain name
//        as the only argument.
//
//   To use this script as an app:
//   - Add to Column A of a Google Spreadsheet in a tab named "Domains".
//   - Substitute the Spreadsheet key to the spreadsheet_key variable below.
//   - Substitute the Sheet name to the sheet_name variable below.
//   - Make sure Column B is empty (we write to it)
//
//     NOTE: Domains which are unverified Apps domains will appear in this
//           output as "Not Provisioned in GApps" until the domain is verified.
//
//   To use this script as a function:
//     Add the function to a cell by entering:
//       =IsGAppsDomain("example.com")
//
//      The result will be TRUE or FALSE.


function checkDomainInventory() {
  var spreadsheet_key = "YOUR_SPREADSHEET_KEY";
  var sheet_name = "YOUR_SHEET_NAME";
  var num_data_columns = 1;
  var spreadsheet = SpreadsheetApp.openById(spreadsheet_key);
  var sheet = spreadsheet.getSheetByName(sheet_name);
  var data_range = sheet.getDataRange();

  // Make sure column A has contents
  if (data_range.getNumColumns() < num_data_columns) {
    Logger.log("Input Sheet has too few columns.  Exiting");
    return;
  }
  var values = data_range.getValues();
  for (var i=0; i < values.length; i++) {
    if (IsGAppsDomain(values[i][0])) {
      sheet.getRange(i+1, 2, 1, 1)
           .setValue("Is Provisioned in GApps")
           .setBackgroundColor("Green")
           .setFontColor("White");
    } else {
      sheet.getRange(i+1, 2, 1, 1)
           .setValue("Not Provisioned in GApps")
           .setBackgroundColor("Red");
    }
  }
}


function IsGAppsDomain(domain) {
  var re_match_negative = new RegExp(
     "you've reached a login page for a domain that isn't using Google Apps");
  var response = UrlFetchApp.fetch("https://mail.google.com/a/" + domain);
  return(! re_match_negative.test(response.getContentText()));
}
