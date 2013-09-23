#!/usr/bin/perl

#
# Connect to the Provisioning API
# - Dump list of groups
# - Dump members for each group
#

use LWP::UserAgent;

# Get Auth Token, do not expose below DocRoot
require("./api-global.pl");

$token = &getToken;

my @groups = &getAllGroups($domain, $token);
&iterate(@groups);


sub iterate {
	my @array = @_;
	my $csv = 1;  # output to CSV file

	foreach my $url (@array) {
		my @parts = split(/\//, $url);
		my $group = $parts[-1];
		my $cleanName = $group;
		$cleanName =~ s/\%40$domain//;

		if ($csv) {
			foreach my $member (&getGroupMembers($group, $domain, $token)) {
				print "$cleanName,$member\n";
			}
		}
		else {
			print "-------------------------------------------\n";
			print "Group Name: $cleanName \n\n";
			foreach my $member (&getGroupMembers($group, $domain, $token)) {
				print $member . "\n";
			}
			print "\n";
		}
	}
}

sub getAllGroups {
	my ($domain, $token) = @_;
	my $url = "https://apps-apis.google.com/a/feeds/group/2.0/$domain";
	my @groups = ();

	my $code = "$url\n\n";
	my $xml .= &sendGet($url, $token);

	$xml =~ s/>/>\n/g;
	foreach my $line (split(/\n/, $xml)) {
		#print $line . "\n";

		if ($line =~ /^http.*<\/id>$/) {
			chomp($line);
			$line =~ s/<\/id>//;
			push @groups, $line;
		}
	}

	shift(@groups);  # first element is just the domain name
	return @groups;	
}

sub getGroupMembers {
	my ($group, $domain, $token) = @_;
	my $url = "https://apps-apis.google.com/a/feeds/group/2.0/$domain/$group/member";
	my $xml = &sendGet($url, $token);
	my @members = ();

	$xml =~ s/>/>\n/g;
	foreach my $line (split(/\n/, $xml)) {
		if ($line =~ /<apps:property name='memberId'/) {
			$line =~ s/<apps:property name='memberId' value='//;
			$line =~ s/'.*$//;

			push @members, $line;
		}
	}

	return @members;
}


