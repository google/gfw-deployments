var UserCreateController = function($location) {
  this.$location = $location;
};

UserCreateController.prototype.next = function() {
  this.$location.path('/step5_confirm');
};

angular.module(CONTROLLERS).controller('UserCreateController',
  UserCreateController);
