# Rapid Reseller

An end to end demonstration application that provisions a resold Google Apps domain.

## DISCLAIMER

   (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
   WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
   WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
   PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND

   (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA
   , OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
   DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
   GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
   THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR
   ITS DERIVATIVES.

## Getting Started

### Prerequisites

Generate an OAuth2 project. ( https://code.google.com/apis/console/ )

From the services tab, activate the following:

  - "Google Apps Reseller API"
  - "Admin SDK"
  -  "Site Verification API"

Add a new API Client ID from the console:

  - Select the service account mechanism
  - Download the p12 private key.

Convert the P12 key into PEM format:
    
    openssl pkcs12 -in xxxxx.p12 -nodes -nocerts > privatekey.pem

Adjust 'settings.py' to reflect the API Client ID, Service Account Email Address, and private key location.

Authorize the Client ID in the Google Apps Control Panel for the reseller domain.
  ( Security -> Advanced Settings -> Manage Third Party OAuth )

For the client name, utilize the Client ID from the API project.

Add the following scopes:
  -  https://www.googleapis.com/auth/apps.order
  -  https://www.googleapis.com/auth/siteverification
  -  https://apps-apis.google.com/a/feeds/user/
  -  https://www.googleapis.com/auth/admin.directory.user

### Requirements

- NPM - Node Package Manager, installs with NodeJS (http://nodejs.org)
- Bower, installed by NPM
- Grunt, installed by NPM
- Google App Engine SDK
- (Mac Users Only) XCode Command Line Tools.

### Mac OS X Users Only

Install the XCode command line tools

    xcode-select --install

### Install the Grunt CLI

Install grunt-cli globally.

    sudo npm install -g grunt-cli

### Install Bower

Bower is a package manager for client-side javascript

    sudo npm install -g bower

### Installing Dev Dependencies

Navigate to the root directory and run the following command.
This shell script is build for UNIX-like OSes.
Windows users will probably have do something special.

    sh setup.sh

### Get Started

Start the main grunt task:

    grunt dev

This will watch for changes to non-vendor javascript and css.

### Deploying a build

Utilize the following grunt task to compile and uglify the JS

    grunt build:prod