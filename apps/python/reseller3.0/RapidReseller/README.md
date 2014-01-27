# Rapid Reseller

An end to end demonstration application that provisions a resold Google Apps domain.

## Getting Started

### Requirements

- NPM - Node Package Manager, installs with NodeJS (http://nodejs.org)
- Bower, installed by NPM
- Grunt, installed by NPM
- Google App Engine SDK

### Install the Grunt CLI

Install grunt-cli globally.

    npm install -g grunt-cli

### Install Bower

Bower is a package manager for client-side javascript

    npm install -g bower

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