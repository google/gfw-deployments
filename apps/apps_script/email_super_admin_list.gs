// Reference Implementation of Apps Script that emails
// a list of Super Administrators for a periodic audit.
//
//###########################################################################
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
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
//
// NOTE: As written, this only looks for Super Administrators, versus
//       other users with delegated admin access.
//
// The email body lists each user with a comma separated list of these fields:
//   - First Name
//   - Last Name
//   - Username (without domain)

var AUDIT_EMAIL_ADDRESS = 'audit@domain.com';
var EMAIL_SUBJECT_LINE= 'List of Google Apps Super Admin Users';

function mailListOfSuperAdminUsers() {
  
  var emailContent = "";
  
  var users = UserManager.getAllUsers();
  for (var i in users) {
    if (users[i].getIsAdmin()) {
      var attributes = [users[i].getGivenName(),
                        users[i].getFamilyName(),
                        users[i].getUsername()];
      emailContent += attributes.join() + "\n";
    }
  }
  
  if (emailContent.length > 0) {
    GmailApp.sendEmail(AUDIT_EMAIL_ADDRESS, EMAIL_SUBJECT_LINE, emailContent);
  } 
}
