// The following script will load members to groups based on entries
// given in a Google Spreadsheet.
//
// Usage:
//   - Add member mappings to a Google Spreadsheet in a tab named "Members".
//   - Substitute the Spreadsheet key to the spreadsheet_key variable below.
//   - Make sure the group email is in column A and the member email is in
//     column B.  Use the full email address for each.
//   - In column C, this script will write whether the membership addition
//     was successful or not.
//
// NOTE: If the group does not exist, it will not be created and the
//       record will be skipped.
function addGroupMembers() {
  var spreadsheet_key = "0Au3xP4rxIKlHdFlCMy0ybFVoSzNfSzgwb3lrWVBVNF";
  var sheet_name = "Members";
  var num_data_columns = 2;

  var spreadsheet = SpreadsheetApp.openById(spreadsheet_key);
  var sheet = spreadsheet.getSheetByName(sheet_name);
  var data_range = sheet.getDataRange();

  if (data_range.getNumColumns() < num_data_columns) {
    Logger.log("Input Sheet has too few columns.  Exiting");
    return;
  }

  var values = data_range.getValues();
  for (var i=0; i < values.length; i++) {
    try {
      Logger.log("Loading group [" + values[i][0] + "]");
      var group = GroupsManager.getGroup(values[i][0]);
      Logger.log("Adding member [" + values[i][1] +
                 "] to group [" + values[i][0] + "]");
      group.addMember(values[i][1]);
      sheet.getRange(i+1, 3, 1, 1).setValue("SUCCESS: Added member");
    } catch(err) {
      Logger.log("ERROR: Could not add [" + values[i][1] +
                 "] to group [" + values[i][0] + "]" +
                 err.message);
      sheet.getRange(i+1, 3, 1, 1).setValue("ERROR: Failed to add member");
    }
  }
}
