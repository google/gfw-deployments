<?php
    // Start the session.
    session_start();

    // Establish global configurations.
    global $SETTINGS;
    global $GOOGLE_CLIENT_CONFIG;

    $SETTINGS = array(
        'ROOT'              => dirname(__FILE__),
        'OAUTH2_CLIENT_ID'  => 'CLIENT ID HERE',
        'OAUTH2_SERVICE_ACCOUNT_EMAIL' => "SERVICE ACCOUNT EMAIL HERE",
        'OAUTH2_SCOPES'     => array(
            'https://www.googleapis.com/auth/apps.order',
            'https://www.googleapis.com/auth/siteverification',
            'https://apps-apis.google.com/a/feeds/user/'
        ),
        'OAUTH2_PRIVATE_KEY'    => "privatekey.p12",
        'RESELLER_DOMAIN'       => "RESELLER DOMAIN HERE",
        'RESELLER_ADMIN'        => "RESELLER ADMIN HERE"
    );

    $GOOGLE_CLIENT_CONFIG = array(
        'authClass'     => 'Google_OAuth2',
        // Possible options include Curl or Sockets, see the 'io' folder.
        'ioClass'       => 'Google_HttpStreamIO',
        // Possible options include APC, File, and Memcache, see the 'cache' folder.
        'cacheClass'    => 'Google_MemcacheCache',

        // on AppEngine this value doesn't matter, but will be relevant on a traditional LAMP stack.
        'ioMemCacheCache_host'  => 'memcache_host',
        'ioMemCacheCache_port'  => '37337'
    );
?>