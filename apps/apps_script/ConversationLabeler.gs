// ConversationLabeler
//
//   Copyright 2013 Google Inc. All Rights Reserved.
//
//   Adds a label to any message that has been replied to or 
//   forwarded. The most common use case for this is with users that
//   have turned off 'Conversation View' in their Gmail Settings.
//
//   NOTE: When using 'Conversation View', coversations that have been
//         replied to or dorwarded will stay in the "Replied to" and
//         'Forwarded' labels even if subsequent messages are received.
/*

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

###########################################################################
DISCLAIMER:

(i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND

(ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR
ITS DERIVATIVES.
###########################################################################

*/
//
// SETUP:
//   1. User should run 'ConversationLabeler once manually in order to 
//      authorize the application and create labels.
//      It is fine if the user configures the "Response Automation"
//      label to always be hidden.
//   2. The user creates a filter:
//        "from:me AND (subject:Fwd OR subject:Re)"
//      which applies the "Response Automation" label.
//   3. The user implements a Trigger, launching the Apps Script function
//        ConversateionLabeler()
//      once every thirty minutes.

function ConversationLabeler() {
  GmailApp.createLabel('Forwarded');
  
  var user = Session.getActiveUser().getEmail();
  
  var forward = __GetOrCreateLabel('Forwarded');
  var replied = __GetOrCreateLabel('Replied');
  // Label for unprocessed messages.
  var automation = __GetOrCreateLabel('Response Automation');
  
  var threads = automation.getThreads();

  // Iterate through all threads in the 'Response Automation' label.
  for(var thread_i = 0; thread_i < threads.length; ++thread_i) {
    var thread = threads[thread_i];
    var messages = thread.getMessages();

    // Iterate through all messages in the thread, from newest to
    // oldest.    
    for(var message_i = messages.length - 1; message_i > 0; --message_i) {
      var message = messages[message_i];

      // Ignore the message if it's a draft.
      if(! message.isDraft() && message.getFrom().indexOf(user) >= 0) {
        // The message was sent by the script runner.
        var prefix = (message.getSubject().toLowerCase().split(':'))[0];
        if(prefix == 'fwd') {
          // The message was forwarded. Add our 'Forwarded' label.
          thread.addLabel(forward);
        }
        
        if(prefix == 're') {
          // The message was a reply. Add our 'Reply' label.
          thread.addLabel(replied);
        }
      }
    }

    // Remove the 'Response Automation' label; we've finished processing it.    
    thread.removeLabel(automation);
  }
}

function __GetOrCreateLabel(label_name) {
  var label = GmailApp.getUserLabelByName(label_name);
  
  if(! label) {
    label = GmailApp.createLabel(label_name);
  }

  return label;
}
