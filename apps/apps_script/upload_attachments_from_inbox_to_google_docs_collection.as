// Reference Implementation of Apps Script that searches
// a user's inbox for unread messages looking for PDF attachments.
// For each attachment found, it uploads the file in a user defined
// collection.
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
// This script can be used when files are being emailed to a
// shared mailbox and the customer needs those attachments
// shared with a specific group of people.
//
// Usage:
//       - First define a Google Collection and share that collection
//         with a Google Group comprised of those that should have access
//         to the documents.  Capture the ID for that collection from the URL.
//       - Next open a new Google Spreadsheet as the user/mailbox that will be receiving
//         the messages.
//       - Go to Tools->Script Editor->Create A Project.  Name it something appropriate.
//         then copy in the contents of this code.  Edit the ACL_TEST_COLLECTION_ID
//         variable and insert the ID from Step 1.
//       - Choose the function AddDocsToGroupACL from the list of functions to run and
//         press the blue "play" button.  This should prompt you to provide privileges
//         for this script.
//       - Next add a trigger for this script to run.  In the Apps Script editor window,
//         go to Triggers->Current Script's triggers...  Select "Add new Trigger".
//         Use an Events:Time Driven trigger, define the interval and make sure to set a
//         notification recipient for errors in running the script.


// Global Variables
var ACL_TEST_COLLECTION_ID = "0B-3xP4rxIKlHM2JmYTc5YzEt;lkjasldkjf;lkjasdfMtNDFhMmRmMDhhZmZh";
var CONTENT_TYPE = "application/pdf";
var GMAIL_SEARCH_OPERATORS = "label:inbox is:unread";

function AddDocsToGroupACL() {

  // Get the Collection we will add docs to
  var acl_collection = DocsList.getFolderById(ACL_TEST_COLLECTION_ID);
  Logger.log(acl_test_collection.getName());

  // Search the inbox for unread messages
  var new_messages = GmailApp.search(GMAIL_SEARCH_OPERATORS);
  for (var o = 0; o < new_messages.length; ++o) {
    var messages_in_thread = new_messages[o].getMessages();
    for (var i = 0; i < messages_in_thread.length; ++i) {
      Logger.log(messages_in_thread[i].getSubject());
      var attachments_blobs = messages_in_thread[i].getAttachments();
      for (var a = 0;a < attachments_blobs.length; ++a) {
        Logger.log(attachments_blobs[a].getContentType());
        if (attachments_blobs[a].getContentType() == CONTENT_TYPE) {
          // Create the file in the specified docs collection
          acl_collection.createFile(attachments_blobs[a]);
        }
      }

      // Mark them as read
      messages_in_thread[i].markRead();

    }
  }
}
