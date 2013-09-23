/*********************************************************************
*                            DriveScoop                              *
**********************************************************************
   A Google Apps Script that automatically moves messages and
   attachments from labels in the Scoop hierarchy to folders in
   Google Drive.
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
   4. Create a new file named 'DriveScoop'.
   5. In the editor pane, with the 'DriveScoop.gs' tab selected, paste
      the full contents of this script.
   6. In Gmail, create a label called "Scoop".
   7. Create labels nested under the "Scoop" label, each of which will
      be processed by DriveScoop.
   8. Optionally create filters to automate placing messages of a
      particular sort in a Scoop label.addToThread(
   9. Back in the Script Editor, click 'Run' > 'DriveScoop' and grant
      DriveScoop with authorization to modify your Drive contents and
      your Gmail by clicking 'Authorize' and/or 'Grant Access'.
  10. Back in the Script Editor, click 'Resources' > 'Current Script's
      Triggers'.
  11. Set up a trigger to run 'DriveScoop' as a 'Time-driven' script
      using the 'Hours timer' set for 'Every hour'.
  12. Optionally add a 'notification' to alert of any script run-time
      issues.
  13. Click 'Save' and this script should begin to function.
**********************************************************************
*                      OPERATING INSTRUCTIONS                        *
**********************************************************************
   Any message that gets placed in a label under Scoop should be
   added as a Google Doc (including attachments) in a Drive folder of
   the same name as the Scoop label.
*********************************************************************/
function DriveScoop() {
  // Needed shorter names to maintain a max line length of 70.
  var paragraph_heading = DocumentApp.ParagraphHeading;
  var attribute = DocumentApp.Attribute;

  // Iterate through each label, looking only for ones beginning
  // with Scoop.
  var labels = GmailApp.getUserLabels();
  for(label_number = 0;
      label_number < labels.length;
      label_number++) {
    var label = labels[label_number];
    var label_name = label.getName();
    var label_match = label_name.match(/^Scoop\//);
    if(label_match) {
      var folder_name = label_name.slice(label_match[0].length);

      var folder = GetFolderIfExists(folder_name);
      if(! folder) {
        folder = DocsList.createFolder(folder_name);
      }

      // Iterate through ten threads at a time. I don't remember
      // why...
      var thread_batch = 10;
      var thread_start = 0;
      var thread_end = false;
      while(thread_end == false) {
        var threads = label.getThreads(thread_start, thread_batch);

        if(threads.length < thread_batch) {
          thread_end = true;
        }

        for(var thread_count = 0;
            thread_count < threads.length;
            thread_count++) {
          var thread = threads[thread_count];
          var messages = thread.getMessages();

          // Iterate through each message in the thread.
          for(var message_count = 0;
              message_count < messages.length;
              message_count++) {
            var message = messages[message_count];
            var attachments = message.getAttachments();
            if(attachments.length == 0) {
              message.moveToTrash();
              continue;
            }

            // Grab the message's headers.
            var from = message.getFrom();
            var subject = message.getSubject();
            var to = message.getTo();
            var cc = message.getCc();
            var date = message.getDate();
            var body = message.getBody();

            // Begin creating a doc.
            var document = DocumentApp.create(subject +
                                              " [" + date + "]");

            var document_title = document.appendParagraph(subject);

            document_title.setHeading(paragraph_heading.HEADING1);
            var style = {};
            style[attribute.HORIZONTAL_ALIGNMENT] = (
              DocumentApp.HorizontalAlignment.CENTER);
            document_title.setAttributes(style);

            var headers_heading = (
              document.appendParagraph("Key Message Headers"));
            headers_heading.setHeading(
              DocumentApp.ParagraphHeading.HEADING2);

            AddHeaderToDoc(document, "From", from);
            AddHeaderToDoc(document, "To", to);
            AddHeaderToDoc(document, "Cc", cc);
            AddHeaderToDoc(document, "Date", date);
            AddHeaderToDoc(document, "Subject", subject);

            if(attachments.length) {
              var attachments_heading = (
                document.appendParagraph("Attachments"));
              attachments_heading.setHeading(
                paragraph_heading.HEADING2);

              for(var attachment_count = 0;
                  attachment_count < attachments.length;
                  attachment_count++) {
                var attachment = attachments[attachment_count];

                var file = folder.createFile(attachment);
                Utilities.sleep(1000);

                var attachment_name = file.getName();
                var attachment_url = file.getUrl();

                var paragraph = (
                  document.appendParagraph(attachment_name));
                paragraph.setIndentStart(72.0);
                paragraph.setIndentFirstLine(36.0);
                paragraph.setSpacingBefore(0.0);
                paragraph.setSpacingAfter(0.0);
                paragraph.setLinkUrl(attachment_url);
              }
            }

            var body_heading = (
              document.appendParagraph("Body (without Markup)"));
            body_heading.setHeading(paragraph_heading.HEADING2);

            var sanitized_body = body.replace(/<\/div>/, "\r\r");
            sanitized_body = sanitized_body.replace(/<br.*?>/g, "\r");
            sanitized_body = sanitized_body.replace(/<\/p>/g, "\r\r");
            sanitized_body = sanitized_body.replace(/<.*?>/g, "");
            sanitized_body = sanitized_body.replace(/&#39;/g, "'");
            sanitized_body = sanitized_body.replace(/&quot;/g, '"');
            sanitized_body = sanitized_body.replace(/&amp;/g, "&");
            sanitized_body = sanitized_body.replace(/\r\r\r/g,
                                                    "\r\r");
            var paragraph = document.appendParagraph(sanitized_body);

            var body_heading = (
              document.appendParagraph("Body (original)"));
            body_heading.setHeading(paragraph_heading.HEADING2);

            var paragraph = document.appendParagraph(body);

            var id = document.getId();
            document.saveAndClose();

            var document_record = DocsList.getFileById(id);
            document_record.addToFolder(folder);

            message.moveToTrash();
          }
        }

        thread_start += threads.length;
      }
    }
  }
}


function GetFolderIfExists(folder_name) {
/* Specify a Folder object by name.

   Arguments:
     folder_name: a String containing the name of a
                  folder

   Returns:
     If the folder exists, returns the folder as a Folder object, otherwise
     returns null.
*/
  var folders = DocsList.getFolders();

  for(var folder_number = 0;
      folder_number < folders.length;
      folder_number++) {
    var folder = folders[folder_number];
    if(folder_name == folder.getName()) {
      return folder;
    }
  }

  return null;
}


function AddHeaderToDoc(document, header_name, header_value) {
/* Adds a formatted Email header to a Google Doc.

   Arguments:
     document: a Document object to add the header to
     header_name: a String containing the name of the header
     header_value: a String containing the value of the header

   Returns:
     Nothing
*/
  if(header_value) {
    var paragraph = document.appendParagraph("");
    paragraph.setIndentStart(72.0);
    paragraph.setIndentFirstLine(36.0);
    paragraph.setSpacingBefore(0.0);
    paragraph.setSpacingAfter(0.0);

    var name = paragraph.appendText(header_name + ": ");
    name.setBold(false);
    var value = paragraph.appendText(header_value);
    value.setBold(true);
  }
}
