var CustomerController = function($http,
                                  $location,
                                  AlertChannelService,
                                  CurrentDomainService) {
  var domain = 'demo-' + new Date().getTime() + '.resold.richieforeman.net';
  this.customerDomain = domain;
  this.alternateEmail = 'nobody@google.com';
  this.phoneNumber = '212.565.0000';
  this.contactName = 'A Googler';
  this.organizationName = 'Google Demo Company';
  this.locality = 'NYC';
  this.region = 'NY';
  this.countryCode = 'US';
  this.postalCode = '11101';
  this.addressLine1 = '76 9th Ave';

  this.$http = $http;
  this.$location = $location;
  this.$alertChannelService = AlertChannelService;
  this.$currentDomainService = CurrentDomainService;
}

CustomerController.prototype.submit = function() {
  var self = this;

  self.$http.post('/api/createCustomer', {
    'domain': self.customerDomain,
    'alternateEmail': self.alternateEmail,
    'phoneNumber': self.phoneNumber,
    'postalAddress.contactName': self.contactName,
    'postalAddress.addressLine1': self.addressLine1,
    'postalAddress.organizationName': self.organizationName,
    'postalAddress.locality': self.locality,
    'postalAddress.region': self.region,
    'postalAddress.countryCode': self.countryCode,
    'postalAddress.postalCode': self.postalCode
  }).success(function(data, status, headers, config) {
      self.$currentDomainService.set(self.customerDomain);
      self.$location.path('/step2');
  }).error(function(data, status, headers, config) {
      self.$alertChannelService.Alert(data.message);
  });
};

angular.module(CONTROLLERS).controller('CustomerController',
  CustomerController);