mod = angular.module(CONTROLLERS);

mod.controller('CustomerController', function($http,
                                              $location,
                                              AlertChannelService,
                                              CurrentDomainService) {
  var self = this;
  // Set a sensible default domain.
  var domain = 'demo-' + new Date().getTime() + '.resold.richieforeman.net';
  self.customerDomain = domain;
  self.alternateEmail = 'nobody@google.com';
  self.phoneNumber = '212.565.0000';
  self.contactName = 'A Googler';
  self.organizationName = 'Google Demo Company';
  self.locality = 'NYC';
  self.region = 'NY';
  self.countryCode = 'US';
  self.postalCode = '11101';
  self.addressLine1 = '76 9th Ave';

  self.submit = function() {

    $http.post('/api/createCustomer', {
      'domain': this.customerDomain,
      'alternateEmail': this.alternateEmail,
      'phoneNumber': this.phoneNumber,
      'postalAddress.contactName': this.contactName,
      'postalAddress.addressLine1': this.addressLine1,
      'postalAddress.organizationName': this.organizationName,
      'postalAddress.locality': this.locality,
      'postalAddress.region': this.region,
      'postalAddress.countryCode': this.countryCode,
      'postalAddress.postalCode': this.postalCode
    }).success(function(data, status, headers, config) {
        CurrentDomainService.set(self.customerDomain);
        $location.path('/step2');
      }).error(function(data, status, headers, config) {
        AlertChannelService.Alert(data.message);
      });

  };
});
