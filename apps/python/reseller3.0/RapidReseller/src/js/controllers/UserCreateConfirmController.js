mod = angular.module(CONTROLLERS);

var UserCreateConfirmController = function($location, $http,
                                           AlertChannelService,
                                           CurrentDomainService) {
  var self = this;

  self.$location = $location;
  self.$http = $http;
  self.$alertChannelService = AlertChannelService;
  self.$currentDomainService = CurrentDomainService;

  self.userStatus = -1;

  // Create a user as the controller loads.
  self.createUser();
};

UserCreateConfirmController.prototype.next = function() {
  this.$location.path('/step6');
}

UserCreateConfirmController.prototype.createUser = function() {
  var self = this;
  self.$http.post('/api/createUser', {
    domain: self.$currentDomainService.get()
  }).success(function(data, status, headers, config) {
    self.userStatus = 1;
    self.username = data.username;
    self.password = data.password;
  }).error(function(data, status, headers, config) {
    self.userStatus = 0;
    var msg = 'Error when creating user: ' + data.message;
    self.$alertChannelService.Alert(msg);
  });
};

angular.module(CONTROLLERS).controller('UserCreateConfirmController',
  UserCreateConfirmController);
