#!/usr/bin/perl -w

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
              'service' => 'apps'
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
# Create and Send a PUT request
#
sub sendPut {
        my ($url, $data, $token) = @_;
        my $output = '';

        # Create an LWP object to make the HTTP request
        my $lwp_object = LWP::UserAgent->new;
        push @{ $lwp_object->requests_redirectable }, 'PUT';

        my $update = HTTP::Request->new(
                PUT => $url,
                HTTP::Headers->new(Content_Type => 'application/atom+xml', "Authorization" => "GoogleLogin auth=$token"),
                $data);
        my $response = $lwp_object->request($update);

        #die "$url error: ", $response->status_line unless $response->is_success;
        $output .= "'$url' error: \n" . $response->status_line . "\n";

        $output .= $response->content;

        return $output;
}

#
# Create and Send a DELETE Request
#
sub sendDelete {
        my ($url, $token) = @_;
        my $output = '';

        # Create an LWP object to make the HTTP request
        my $lwp_object = LWP::UserAgent->new;
        push @{ $lwp_object->requests_redirectable }, 'PUT';

        my $update = HTTP::Request->new(
                DELETE => $url,
                HTTP::Headers->new("Authorization" => "GoogleLogin auth=$token"),
                $data);
        my $response = $lwp_object->request($update);

        #die "$url error: ", $response->status_line unless $response->is_success;
        $output .= "'$url' error: \n" . $response->status_line . "\n";

        $output .= $response->content;

        return $output;

}

#
# Create and Send a POST Request
#
sub sendPost {
        my ($url, $data, $token) = @_;
        my $output = '';

        # Create an LWP object to make the HTTP request
        my $lwp_object = LWP::UserAgent->new;
        push @{ $lwp_object->requests_redirectable }, 'POST';

        my $update = HTTP::Request->new(
                POST => $url,
                HTTP::Headers->new(Content_Type => 'application/atom+xml', "Authorization" => "GoogleLogin auth=$token"),
                $data);
        my $response = $lwp_object->request($update);

        #die "$url error: ", $response->status_line unless $response->is_success;
        $output .= "'$url' error: \n" . $response->status_line . "\n";

        $output .= $response->content;

        return $output;
}

#
# Create and Send a GET Request
#
sub sendGet {
        my ($url, $token) = @_;
        my $output = '';

        # Create an LWP object to make the HTTP request
        my $lwp_object = LWP::UserAgent->new;
        push @{ $lwp_object->requests_redirectable }, 'POST';

        my $update = HTTP::Request->new(
                GET => $url,
                HTTP::Headers->new("Authorization" => "GoogleLogin auth=$token"),
                $data);
        my $response = $lwp_object->request($update);

        #die "$url error: ", $response->status_line unless $response->is_success;
        $output .= "'$url' error: \n" . $response->status_line . "\n";

        $output .= $response->content;

        return $output;
}

1;

