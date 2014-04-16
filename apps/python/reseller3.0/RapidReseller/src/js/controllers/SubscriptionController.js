var SubscriptionController = function($rootScope, $http, $location,
                                      AlertChannelService,
                                      CurrentDomainService) {
  this.numberOfSeats = 5;
  this.$http = $http;
  this.$location = $location;
  this.$alertChannelService = AlertChannelService;
  this.$currentDomainService = CurrentDomainService;
};

SubscriptionController.prototype.submit = function() {
  var self = this;
  self.$http.post("/api/createSubscription", {
    numberOfSeats: self.numberOfSeats,
    domain: self.$currentDomainService.get()
  }).success(function(data, status, headers, config) {
      self.$location.path("/step3");
  }).error(function(data, status, headers, config) {
      self.$alertChannelService.Alert(data.message);
  });
};

angular.module(CONTROLLERS).controller('SubscriptionController',
  SubscriptionController);