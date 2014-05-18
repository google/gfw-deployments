<?php
// Start the session.
session_start();

set_include_path("google-api-php-client/src/" . PATH_SEPARATOR . get_include_path());

require_once 'Google/Client.php';
require_once 'Google/Service/Reseller.php';
require_once 'Google/Service/Directory.php';
require_once 'Google/Service/SiteVerification.php';

// Establish global configurations.
global $SETTINGS;

$SETTINGS = array(
  'ROOT'              => dirname(__FILE__),
  'OAUTH2_CLIENT_ID'  => '',
  'OAUTH2_SERVICE_ACCOUNT_EMAIL' => "",
  'OAUTH2_SCOPES'     => array(
    Google_Service_Reseller::APPS_ORDER,
    Google_Service_SiteVerification::SITEVERIFICATION,
    Google_Service_Directory::ADMIN_DIRECTORY_USER,
    // Google Licensing service definition does not currently
    // include a constant.
    'https://www.googleapis.com/auth/apps.licensing'
  ),
  'OAUTH2_PRIVATE_KEY'    => "privatekey.p12",
  'RESELLER_DOMAIN'       => "",
  'RESELLER_ADMIN'        => ""
);

if(preg_match("/Development/", $_SERVER['SERVER_SOFTWARE'])) {
  @include_once "settings_local.php";
}
?>