#!/usr/bin/perl

#
# Suspend users from a text file list
#

require("./api-global.pl");

$token = &getToken;

#print "Domain: $domain\n";
#print "Token: $token\n\n";

# Usernames only, one per line, no leading/trailing characters
if ($ARGV[0] ne '') { $file = $ARGV[0]; chomp($file); }
else { $file = 'userlist.csv'; }

open(TXT, "$file");
@users = <TXT>;
close(TXT);


#
# Iterate through the CSV
#
foreach my $line (@users) {
	chop($line);  # remove newline character
	$line =~ s/\r//g;
	$line =~ s/\n//g;
	my ($username, $junk) = split(/,/, $line);

	print &unsuspendUser($username, $domain, $token);
}

#
# Construct XML and POST to API
#
sub unsuspendUser {
	my ($username, $domain, $token) = @_;

	# create a user
	# PUT https://apps-apis.google.com/a/feeds/$domain/user/2.0/$username
	my $url = "https://apps-apis.google.com/a/feeds/$domain/user/2.0/$username";

	my $data = `cat xml/unsuspend.xml`;
	$data =~ s/X_USERNAME_X/$username/g;

	return &sendPut($url, $data, $token);

}

