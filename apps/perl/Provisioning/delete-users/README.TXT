Files:
  api-global.pl - library
  delete.pl - the magic
  userlist.txt - list of users, one per line (default file used)

Steps:
1. Update admin credentials in api-global.pl
2. Create a list of users to be deleted
3. ./delete.pl userlist.txt

The delete.pl script will delete users from a Google Apps domain in bulk, taken from a list of users in a text file.