/*********************************************************************
*                            DriveThis                               *
**********************************************************************
   A Google Apps Script that allows you to save Gmail attachments to
   Google Drive by starring any newly-received message with
   attachments.
**********************************************************************
*                      LICENSING AND DISCLAIMER                      *
**********************************************************************
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
  
   http://www.apache.org/licenses/LICENSE-2.0
  
   DISCLAIMER:

   (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS"
   WITHOUT ANY WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR
   OTHERWISE, INCLUDING, WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF
   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-
   INFRINGEMENT; AND

   (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES,
   PROFIT OR DATA, OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL,
   INCIDENTAL OR PUNITIVE DAMAGES, HOWEVER CAUSED AND REGARDLESS OF
   THE THEORY OF LIABILITY, EVEN IF GOOGLE HAS BEEN ADVISED OF THE
   POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF THE USE OR INABILITY
   TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR ITS
   DERIVATIVES.
**********************************************************************
*                     INSTALLATION INSTRUCTIONS                      *
**********************************************************************
   1. Create (or reuse) a Google Spreadsheet.
      Recommend using one called "Gmail Automation".
   2. In the spreadsheet, click 'Tools' > 'Script Editor'.
   3. In the Script Editor, click 'File' > 'New' > 'File'.
   4. Create a new file named 'DriveThis'.
   5. In the editor pane, with the 'DriveThis.gs' tab selected, paste
      the full contents of this script.
   6. Edit the two variables in the CUSTOM VARIABLES section below.
   7. In Gmail, create a label with the below (UNSAVED_LABEL) name.
   8. Still in Gmail, create a filter which automatically adds this
      label to any message that has attachments (just click 
      "has attachment" in the filter pane and automatically add the
      (UNSAVED_LABEL) label).
   9. In Drive, create a folder with the below (SAVED_FOLDER) name.
  10. Back in the Script Editor, click 'Run' > 'Drive This' and grant
      DriveThis with authorization to modify your Drive contents and
      your Gmail by clicking 'Authorize' and/or 'Grant Access'.
  10. Back in the Script Editor, click 'Resources' > 'Current Script's
      Triggers'.
  11. Set up a trigger to run 'DriveThis' as a 'Time-driven' script
      using the 'Minutes timer' set for 'Every minute'.
  12. Optionally add a 'notification' to alert of any script run-time
      issues.
  13. Click 'Save' and this script should begin to function.
**********************************************************************
*                      OPERATING INSTRUCTIONS                        *
**********************************************************************
   When you receive a message that has attachments that you would like
   to save to Google Drive, just star the message. After about a
   minute, the attachments will be saved in the (SAVED_FOLDER) folder,
   and the message will no longer be starred.

   **NOTE** - DriveThis works for messages that are starred, not
              entire threads. If you star a thread as opposed to a
              message that contains the attachments you want to save
              to Drive, Gmail actually stars only the most recent
              message in that thread, and DriveThis will only capture
              the attachments of that message.
*********************************************************************/

/*********************************************************************
*                         CUSTOM VARIABLES                           *
*********************************************************************/
   // A Gmail label.
   // **NOTE** - Please only use a label with letters/numbers and
   //            spaces, no special characters.
   var UNSAVED_LABEL = "Unsaved Attachments";

   // A Docs folder.
   var SAVED_FOLDER = "Gmail Attachments";
/********************************************************************/


/*********************************************************************
*                       DriveThis PROGRAMMING                        *
**********************************************************************
*                         DO NOT EDIT BELOW                          *
*********************************************************************/
function DriveThis() {
  var unsaved_label = GmailApp.getUserLabelByName(UNSAVED_LABEL);
  var saved_folder = DocsList.getFolder(SAVED_FOLDER);
  
  var query = "is:starred label:" + UNSAVED_LABEL.replace(" ", "-");

  var thread_batch = 10;
  var thread_start = 0;
  var thread_end = false;
  while(thread_end == false) {
    var threads = GmailApp.search(query, thread_start, thread_batch);

    if(threads.length < thread_batch) {
      thread_end = true;
    }
    
    for(var thread_count = 0;
        thread_count < threads.length;
        thread_count++) {
      var thread = threads[thread_count];    
      var messages = thread.getMessages();
      
      for(var message_count = 0;
          message_count < messages.length;
          message_count++) {
        var message = messages[message_count];
        if(message.isStarred()) {
          var attachments = message.getAttachments();
        
          for(var attachment_count = 0;
              attachment_count < attachments.length;
              attachment_count++) {
            var attachment = attachments[attachment_count];

            try {
              var file = saved_folder.createFile(attachment);
              Utilities.sleep(10000);
            } catch(error) {
              runtime_user = Session.getActiveUser().getUserLoginId();
              GmailApp.sendEmail(runtime_user, "DriveThis error",
                                 "Subject: " + message.getSubject() +
                                 "\nError: " + error.message);
            }
          }
          message.unstar();
        }
      }
      thread.removeLabel(unsaved_label);
    }  
    thread_start += threads.length;
  }
}

