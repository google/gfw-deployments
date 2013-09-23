#!/usr/bin/perl

#
# Create users in bulk from a CSV file
#   CSV format: username,firstname,lastname,password
#

require("./api-global.pl");

$token = &getToken;

print "Domain: $domain\n";
print "Token: $token\n\n";

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
	my ($username, $first, $last, $password) = split(/,/, $line);

	print &createUser($username, $first, $last, $password, $domain, $token);
}

#
# Construct XML and POST to API
#
sub createUser {
	my ($username, $first, $last, $password, $domain, $token) = @_;

	# create a user
	# POST https://apps-apis.google.com/a/feeds/domain/user/2.0
	my $url = "https://apps-apis.google.com/a/feeds/$domain/user/2.0";

	my $data = `cat xml/create.xml`;
	$data =~ s/X_USERNAME_X/$username/g;
	$data =~ s/X_FIRSTNAME_X/$first/g;
	$data =~ s/X_LASTNAME_X/$last/g;
	$data =~ s/X_PASSWORD_X/$password/g;

	#return "$url\n$data\n\n";
	return &sendPost($url, $data, $token);

}

