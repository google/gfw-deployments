api-global.pl - libraries
dump-resources.pl - the magic

Pre-Requisites (uncommon libraries)
- XML::Simple
- Data::Dumper

Steps:
1. Update api-global.pl with domain admin credentials
2. ./dump-resources.pl

The dump-resources.pl script will dump into a CSV in the following format:

    id,Resource-Email,Name,Description,Type

