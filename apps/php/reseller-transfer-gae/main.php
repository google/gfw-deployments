<?php
    /*

    DISCLAIMER:

    (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
    WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
    WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND

    (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
    OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
    DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
    GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
    THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR
    ITS DERIVATIVES.

    */

    /*
        This simple PHP AppEngine application prompts the user for a domain
        and customer transfer token.  The customer is then transferred to
        the management of a specified reseller using the Reseller 3.0 API

        This app could easily be deployed on a traditional LAMP stack.

        Setup:
        - Install the AppEngine SDK.
        - Install the Google API PHP Client
          (https://code.google.com/p/google-api-php-client/)
        - Generate an OAuth2 project.
          ( https://code.google.com/apis/console/ )
        - From the services tab, activate the "Google Apps Reseller API"
        - Add a new API Client ID from the console
          - Select the service account mechanism
          - Download the p12 private key.
        - Adjust 'config.php' to reflect the API Client ID,
          Service Account Email Address, and private key location.
        - Authorize the Client ID in the Google Apps Control Panel
          for the reseller domain.
          ( Security -> Advanced Settings -> Manage Third Party OAuth )

          For the client name, utilize the Client ID from the API project.

          Add the following scopes:
            https://apps-apis.google.com/a/feeds/user/
            https://www.googleapis.com/auth/apps.order
            https://www.googleapis.com/auth/siteverification

    */

    require_once 'config.php';

    // Draw a simple template.
    include 'templates/index.php';
?>