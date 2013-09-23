#!/usr/bin/perl

#
# This is specific to the update-timezone.pl script because
#   of how it handles redirects.
#
use LWP::UserAgent;

$username = 'admin@domain.com';
$password = 'password';
($junk, $domain) = split(/\@/, $username);

sub getToken {
	# Create an LWP object to make the HTTP POST request
	my $lwp_object = LWP::UserAgent->new;

	# Define the URL to submit the request to
	my $url = 'https://www.google.com/accounts/ClientLogin';

	# Submit the request with values for the accountType, Email and Passwd variables.
	my $response = $lwp_object->post($url,
            [ 'accountType' => 'HOSTED',
              'Email' => $username,
              'Passwd' => $password,
	      'source' => 'timezone-updater',
	      'service' => 'cl'
            ]);

	die "$url error: ", $response->status_line unless $response->is_success;

	# Extract the authentication token from the response
	my $auth_token;
	foreach my $line (split/\n/, $response->content) {
    		if ($line =~ m/^Auth=(.+)$/) {
        		$auth_token = $1;
			last;
		}
	}

	return $auth_token;
}

#
# specific to some Calendar PUT methods because LWP::UserAgent
#   does not send PUT after a redirect
#
sub sendPut {
	my ($url, $data, $token) = @_;
	my $output = '';

	# Create an LWP object to make the HTTP request
	my $lwp_object = LWP::UserAgent->new;
	#my $lwp = LWP::UserAgent->new;

	# Make first request to get gsessionid
	my $update = HTTP::Request->new(
		POST => $url,
		HTTP::Headers->new(Content_Type => 'application/atom+xml', "Authorization" => "GoogleLogin auth=$token", "X-HTTP-Method-Override" => "PUT" ),
		$data);

	my $response = $lwp_object->request($update);

	# parse gsessionid
	my $cookie = $response->header("Set-Cookie");
	$cookie =~ s/^.*S=calendar=//;
	$cookie =~ s/;.*$//;

	# request to PUT content
	my $newUrl = $url . "?gsessionid=" . $cookie;
	my $upd2 = HTTP::Request->new(
		POST => $newUrl,
		HTTP::Headers->new(Content_Type => 'application/atom+xml', "Authorization" => "GoogleLogin auth=$token", "X-HTTP-Method-Override" => "PUT" ),
		$data);

	my $resp2 = $lwp_object->request($upd2);

	$output .= "'$url' response: " . $resp2->status_line . "\n";

	return $output;
}

