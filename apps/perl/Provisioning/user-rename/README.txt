api-global.pl - credentials and subroutines that make calls to the Goog
changes.txt - CSV formatted "old-username,new-username"
rename.pl - the magic
update.xml - XML template for formatting UPDATE call to Apps

Steps:

1. Update api-global.pl with domain admin credentials
2. Add source/destination users to CSV file
3. ./rename.pl changes.txt

Any CSV file can be used and specified on the command line, but changes.txt is left in as an example.

