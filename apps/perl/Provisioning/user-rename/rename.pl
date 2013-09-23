#!/usr/bin/perl

use LWP::UserAgent;

# Get Auth Token, do not expose below DocRoot
require("./api-global.pl");

$token = &getToken;

print "Domain: $domain\n";
print "Token: $token\n\n";

# Usernames only, one per line, no leading/trailing characters
if ($ARGV[0] ne '') { $file = $ARGV[0]; chomp($file); }
else { $file = 'userlist.txt'; }

open(TXT, "$file");
@users = <TXT>;
close(TXT);

foreach my $line (@users) {
	chomp($line);  # remove newline character
	$line =~ s/\r//g;
	$line =~ s/\n//g;
	my ($old, $new) = split(/,/, $line);

	my $url = "https://apps-apis.google.com/a/feeds/$domain/user/2.0/$old";

	print "\n";
	print &renameUser($old, $new, $domain, $url, $token);
	print "\n\n";

}


sub renameUser {
	my ($old, $new, $domain, $url, $token) = @_;

	# pull from XML template, search and replace
	my $atom = `cat update.xml`;
	$atom =~ s/X_NEWUSERNAME_X/$new/g;

	print $url . "\n\n";
	print $atom . "\n\n";

	return &sendPut($url, $atom, $token);
}

