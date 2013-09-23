Files:
  api-global.pl - enter credentials in this file
  xml - directory containing XML structure for requests
    filter.xml - XML required to add a filter to a user
    label.xml - XML required to add a label to a user
    sendas.xml - XML required to add a send as address to a user
  update.pl - run this script
  userlist.txt - list of users to run against

Usage:

./update.pl userlist.txt

This script functionality is split in separate files because the code is used on other scripts.  The files required to run the script to add filters to users are included here.

The script currently can perform multiple functions.  All but one are commented out to caution against doing more than one thing at a time.  Eventually command line flags could be used, but I'm too lazy to add them.
