#!/usr/bin/perl

#
# Script to change Calendar Timezones
#   CSV Format: id,name,description.type
#
require("api-specific.pl");

$token = &getToken;

print "Domain: $domain\n";
print "Token: $token\n\n";

# Email,Timezone
if ($ARGV[0] ne '') { $file = $ARGV[0]; chomp($file); }
else { $file = 'users.csv'; }

open(TXT, "$file");
@resources = <TXT>;
close(TXT);

foreach my $line (@resources) {
        chomp($line);  # remove newline character
        $line =~ s/\r//g;
        $line =~ s/\n//g;
        my ($calendar, $tz) = split(/,/, $line);

        print &updateSettings($calendar, $tz, $domain, $token);
}

#
# Make the actual call to create the resource in Apps
#
sub updateSettings {
	my ($calendar, $tz, $domain, $token) = @_;

        my $url = "http://www.google.com/calendar/feeds/default/owncalendars/full/$calendar";
	my $code = '';

	#
	# replace lines in template with CSV values
	#
	my $atom = `cat xml/timezone.xml`;
	$atom =~ s/X_CALENDAR_X/$calendar/g;
	$atom =~ s/X_TIMEZONE_X/$tz/g;

	$code .= &sendPut($url, $atom, $token);

	return $code;
}

