var DriveStorageSubscriptionController = function($http, $location,
                                                  AlertChannelService,
                                                  CurrentDomainService) {
  var self = this;

  self.$http = $http;
  self.$location = $location;
  self.$alertChannelService = AlertChannelService;
  self.$currentDomainService = CurrentDomainService;
};

DriveStorageSubscriptionController.prototype.submit = function() {
  var self = this;

  self.$http.post('/api/createDriveStorageSubscription', {
    domain: self.$currentDomainService.get()
  }).success(function(data, status, headers, config) {
    self.$location.path('/step7');
  }).error(function(data, status, headers, config) {
    var msg = 'Error creating Drive Storage Subscription: ' + data.message;
    self.$alertChannelService.Alert(msg);
  });
};

angular.module(CONTROLLERS).controller('DriveStorageSubscriptionController',
  DriveStorageSubscriptionController);
