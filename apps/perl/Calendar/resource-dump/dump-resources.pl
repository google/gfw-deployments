#!/usr/bin/perl

#
# Get resource list and dump in CSV format
#   CSV Format: id,name,description.type
#

use XML::Simple;
use Data::Dumper;

require("api-global.pl");

$token = &getToken;

#print "Domain: $domain\n";
#print "Token: $token\n\n";
print &getResource($domain, $token);

#
# Get resource list and dump in CSV format
#
sub getResource {
	my ($domain, $token) = @_;
	my $url = "https://apps-apis.google.com/a/feeds/calendar/resource/2.0/$domain/";
	my $code = '';

	# Do the fetch
	my $xml .= &sendGet($url, $token);
	$xml =~ s/^.*\n.*\n//g;  # remove first 2 lines (HTTP response)

	# Parse the returned XML
	$code .= &parseXml($xml);

	return $code;
}

#
# Take in Cal Resource XML and return CSV
#   CSV Format: Id,Name,Resource-Email,Description,Type
#
sub parseXml {
	my ($dump) = @_;
	my $code = '';
	my $xml = new XML::Simple;
	my $data = $xml->XMLin($dump);
	#open(TXT, ">out.txt"); print TXT Dumper($data); close(TXT); # dump the XML for debug

	foreach my $resource (keys %{$data->{entry}}) {
		$code .= $data->{entry}->{$resource}->{'apps:property'}->{resourceId}->{value};
		$code .= ",";
		$code .= $data->{entry}->{$resource}->{'apps:property'}->{resourceCommonName}->{value};
		$code .= ",";
		$code .= $data->{entry}->{$resource}->{'apps:property'}->{resourceEmail}->{value};
		$code .= ",";
		$code .= $data->{entry}->{$resource}->{'apps:property'}->{resourceDescription}->{value};
		$code .= ",";
		$code .= $data->{entry}->{$resource}->{'apps:property'}->{resourceType}->{value};
		$code .= "\n";
	}

	return $code;

}

