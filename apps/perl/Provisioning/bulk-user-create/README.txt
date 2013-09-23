This script will create users in bulk via the Provisioning API:

  http://code.google.com/apis/apps/gdata_provisioning_api_v2.0_developers_protocol.html

Users that already exist will NOT be overwritten or modified, as the API will error out with EntityExists. It is safe to run this more than once against the same set of data.  For high throughput, separate the user list into chunks and run multiple instances.  I have been too lazy to write forks myself.


File List:
  api-global.pl - library
  user-create.pl - the magic
  userlist.csv - example CSV in the necessary format
  xml - directory
    create.xml - XML necessary to POST to the API for a user create

Steps:
1. Update credentials in api-global.pl
2. Create user list in CSV
   - Format: username,firstname,lastname,password
3. ./user-create.pl userlist.csv

