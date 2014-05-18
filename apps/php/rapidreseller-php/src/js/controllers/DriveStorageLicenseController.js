var DriveStorageLicenseController = function($http, $location,
                                             AlertChannelService,
                                             CurrentDomainService) {
  this.$http = $http;
  this.$location = $location;
  this.$alertChannelService = AlertChannelService;
  this.$currentDomainService = CurrentDomainService;
};


DriveStorageLicenseController.prototype.submit = function() {
  var self = this;
  self.$http.post('/api/assignDriveLicense', {
    domain: self.$currentDomainService.get()
  }).success(function(data, status, headers, config) {
    self.$location.path('/done');
  }).error(function(data, status, headers, config) {
    var msg = 'Error assigning Drive Storage License: ' + data.message;
    self.$alertChannelService.Alert(msg);
  });
};
angular.module(CONTROLLERS).controller('DriveStorageLicenseController',
  DriveStorageLicenseController);
