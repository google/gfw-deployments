//Copyright (C) 2012 Google Inc.
//Licensed under the Apache License, Version 2.0 (the "License");
//you may not use this file except in compliance with the License.
//You may obtain a copy of the License at
//
//http://www.apache.org/licenses/LICENSE-2.0
//
//////////////////////////////////////////////////////////////////////////////
//DISCLAIMER:
//
//(i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
//WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
//WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
//PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND
//
//(ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
//OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
//DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
//GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
//THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR ITS
//DERIVATIVES.
//////////////////////////////////////////////////////////////////////////////
//
// Description:
//
// Some users would prefer that the default value for "Guests can:invite others"
// on newly created events be deselected.  The following Apps Script code
// could be set up to periodically look at all events X days forward
// and deselect this checkbox for all events that have the checkbox selected.
//
// The script allows for the end user to define a string of text
// (EXCEPTION_STRING below), such that when the string is found in the
// description of the event, the scanner will skip the event.  Essentially, the
// end user can use this as a signal to the scanner that individual events
// should allow guests to invite others.
//
// Installation:
//
// This script can be embedded in a Google Spreadsheet for the individual user.
//  - Open a new Spreadsheet as the user
//  - Go to Tools -> Script editor..
//  - Paste this code into the new window, then select Save
//  - Enter a name for this project (anything you like)
//  - Edit the DAYS_FORWARD and EXCEPTION_STRING variables to preferred values
//  - Go to the "select function" dropdown and select the function:
//    removeGuestsCanInviteOthers
//  - Press the "Play" button (triangle shaped button)
//  - Follow the screens to authorize the script to access the default calendar.
//  - Go to Triggers -> current script's triggers
//  - Click the link for "No triggers set up. Click here to add one now."
//  - Select the removeGuestsCanInviteOthers function, choose "Time Driven"
//  - Choose the desired interval
//  - Set up a notification for any issues encountered when running the script
//  - Save the configuration and authorize the script to access the calendar


var __author__ = 'mdauphinee@google.com (Matt Dauphinee)'


//  GLOBAL VARIABLES //////////////////////////////////////////
// How many days into the future to check
// event settings.
var DAYS_FORWARD = 365;
// Text, that if found in the event description,
// will signal to the script that the "Guests can: invite others"
// setting should not be manipulated on the event.
var EXCEPTION_STRING = "#allow_invite_others";
///////////////////////////////////////////////////////////////

// Main function to run the scanning of events
function removeGuestsCanInviteOthers() {

  // Calculate the date range to scan
  var start_date = new Date();
  var end_date = new Date();
  end_date.setDate(start_date.getDate() + DAYS_FORWARD);
  Logger.log(start_date);
  Logger.log(end_date);

  var cal = CalendarApp.getDefaultCalendar();
  Logger.log("Checking calendar: " + cal.getName());
  var events = cal.getEvents(start_date, end_date);

  for (var i = 0; i < events.length; ++i) {
    if (_isEligibleEvent(events[i])) {
      if (events[i].guestsCanInviteOthers()) {
        Logger.log("Unchecking 'Guests can: invite others' for event: [" +
                   events[i].getSummary() + "]");
        events[i].setGuestsCanInviteOthers(false);
      }
    }
  }
}

// Based on the presence of EXCEPTION_STRING in event description,
// decides if the event is eligible for setting the
// "Guests can: invite others" value.
function _isEligibleEvent(event) {
  var desc = event.getDescription();
  if (desc.match(EXCEPTION_STRING)) {
    Logger.log("Not eligible: Desc: " + desc);
    return true;
  } else {
    Logger.log("Eligible: Desc: " + desc);
    return false;
  }
}
