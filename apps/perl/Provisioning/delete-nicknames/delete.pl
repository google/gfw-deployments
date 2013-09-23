#!/usr/bin/perl

#
# Bulk delete nicknames from a TXT file
#   1 nickname per line, no leading or trailing characters
#

require("api-global.pl");

$token = &getToken;

# Usernames only, one per line, no leading/trailing characters
if ($ARGV[0] ne '') { $file = $ARGV[0]; chomp($file); }
else { $file = 'nicknamelist.txt'; }

open(TXT, "$file");
@users = <TXT>;
close(TXT);

foreach my $line (@users) {
	# remove newline character, chomp is safer but may not get everything
	chop($line);
	$line =~ s/\r//g;
	$line =~ s/\n//g;

	# Top says TXT file, but CSV parsing left in so list from
	#   Provisioning can be easily used without data conversion
	#
	my ($username, $first, $last, $password) = split(/,/, $line);

	# DELETE nicknames
	print &deleteNickname($username, $domain, $token);
}

sub deleteNickname {
	my ($username, $domain, $token) = @_;
	# DELETE https://apps-apis.google.com/a/feeds/domain/nickname/2.0/nickname
	my $url = "https://apps-apis.google.com/a/feeds/$domain/nickname/2.0/$username";

	my $code = $url . "\n";

	$code .= &sendDelete($url, $token);

	return $code . "\n";
}

