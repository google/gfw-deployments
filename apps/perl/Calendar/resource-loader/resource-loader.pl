#!/usr/bin/perl

#
# Script to load resources into Google Apps from a CSV
#   CSV Format: id,name,description.type
#

require("api-global.pl");

$token = &getToken;

print "Domain: $domain\n";
print "Token: $token\n\n";

# Usernames only, one per line, no leading/trailing characters
if ($ARGV[0] ne '') { $file = $ARGV[0]; chomp($file); }
else { $file = 'list.csv'; }

open(TXT, "$file");
@resources = <TXT>;
close(TXT);

foreach my $line (@resources) {
        chomp($line);  # remove newline character
        $line =~ s/\r//g;
        $line =~ s/\n//g;
        my ($id, $name, $description, $type) = split(/,/, $line);

        print "\n";
        print &createResource($id, $name, $description, $type, $domain, $token);
        print "\n";

}

#
# Make the actual call to create the resource in Apps
#
sub createResource {
	my ($id, $name, $description, $type, $domain, $token) = @_;
        my $url = "https://apps-apis.google.com/a/feeds/calendar/resource/2.0/$domain";
	my $code = '';

	#
	# replace lines in template with CSV values
	#
	my $atom = `cat template.xml`;
	$atom =~ s/X_RESOURCEID_X/$id/;
	$atom =~ s/X_NAME_X/$name/;
	$atom =~ s/X_DESCRIPTION_X/$description/;
	$atom =~ s/X_TYPE_X/$type/;

	$code .= "$name\n";
	$code .= &sendPost($url, $atom, $token);

	return $code;
}

