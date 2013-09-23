#!/usr/bin/perl

#
# Modify user settings via Email Settings API in bulk
#   http://code.google.com/googleapps/domain/email_settings/developers_guide_protocol.html
#

use LWP::UserAgent;

# Get Auth Token, do not expose below DocRoot
require("./api-global.pl");

$token = &getToken;

# Output auth credentials
print "Domain: $domain\n";
print "Token: $token\n\n";

# Each action type may have a different file format
if ($ARGV[0] ne '') { $file = $ARGV[0]; chomp($file); }
else { $file = 'userlist.txt'; }

open(TXT, "$file");
@users = <TXT>;
close(TXT);

#
# Read in each line in the file and make a request
#   via the email settings API
#
foreach my $line (@users) {
  chop($line);  # remove newline character
  $line =~ s/\r//g;
  $line =~ s/\n//g;

  # Each action type may have a different file format
  #  add a label or filter only requires username
  #my ($username, $junk) = split(/,/, $line);
  my ($username, $nickname, $junk) = split(/,/, $line);

  print "$username\n";
  
  # add filter for @domain
  #print &addFilter($username, $domain, $token);

  # add a label for each user
  #print &addLabel($username, $domain, $token);

  # add a send as email address
  print &sendAs($username, $nickname, $domain, $token);
}

sub addFilter {
  my ($username, $domain, $token) = @_;
  my $url = "https://apps-apis.google.com/a/feeds/emailsettings/2.0/$domain/$username/filter";

  my $data = `cat xml/filter.xml`;
  $data =~ s/X_USERNAME_X/$username/g;
  $data =~ s/X_DOMAIN_X/$domain/g;
  $data =~ s/X_FROM_X/\@$domain/g;

  #return "$url\n$data\n\n";
  return &sendPost($url, $data, $token);

}

sub addLabel {
  my ($username, $domain, $token) = @_;
  my $url = "https://apps-apis.google.com/a/feeds/emailsettings/2.0/$domain/$username/label";

  my $data = `cat xml/label.xml`;
  $data =~ s/X_USERNAME_X/$username/g;
  $data =~ s/X_FROM_X/\@$domain/g;

  return &sendPost($url, $data, $token);
}

sub sendAs {
  my ($username, $sendas, $domain, $token) = @_;
  my $url = "https://apps-apis.google.com/a/feeds/emailsettings/2.0/$domain/$username/sendas";

  my $data = `cat xml/sendas.xml`;
  $data =~ s/X_SENDAS_X/$sendas/g;

  return &sendPost($url, $data, $token);
}
