These scripts will update user primary calendar timezones:

  http://code.google.com/apis/calendar/data/2.0/developers_guide_protocol.html#UpdatingCalendars


File List:
  api-specific.pl - Library
  update-timezone.pl - The magic
  users.csv - CSV of user@domain.tld,Timezone/Name
  xml - directory
    timezone.xml - XML template for timezone change

Steps:
1. Update credentials in api-specific.pl
2. Create user list in users.csv
   - Format: user@domain.tld,Timezone/Name
   - Example:   user@appsguy.com,America/Los_Angeles
3. ./update-timezone.pl users.csv

