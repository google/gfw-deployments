These scripts will suspend/unsuspend users in bulk via the Provisioning API:

  http://code.google.com/apis/apps/gdata_provisioning_api_v2.0_developers_protocol.html


File List:
  api-global.pl - Library
  userlist.csv - Text file user list of usernames. Other CSV values will be ignored.  This is a CSV so that the same file format can be used for most scripts.  Newline on the end because I used chop instead of chomp.
  suspend.pl - Script to suspend
  unsuspend.pl - Script to unsuspend
  xml - directory
    suspend.xml - XML required to suspend a user
    unsuspend.xml - XML required to unsuspend a user

Steps:
1. Update credentials in api-global.pl
2. Create user list in userlist.csv
   - Format: username
3a. ./suspend.pl userlist.csv
3b. ./unsuspend.pl userlist.csv

