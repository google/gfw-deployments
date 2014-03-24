mod = angular.module(CONTROLLERS);


mod.controller("SiteVerificationConfirmController", function($location,
                                                             SiteVerificationTokenCacheService) {

  var self = this;

  self.verificationInfo = SiteVerificationTokenCacheService.getData();

  self.next = function() {
    $location.path("/step4");
  };

});

mod.controller("UserCreateController", function($location) {
  var self = this;
  self.next = function() {
    $location.path("/step5_confirm");
  };
});

mod.controller("DriveStorageSubscriptionController", function($http, $location,
                                                              AlertChannelService,
                                                              CurrentDomainService) {
  var self = this;

  self.submit = function() {
    $http.post("/api/createDriveStorageSubscription", {
      domain: CurrentDomainService.get()
    }).success(function(data, status, headers, config) {
        $location.path("/step7");
      }).error(function(data, status, headers, config) {
        AlertChannelService.Alert("Error creating Drive Storage Subscription: " + data.message);
      });
  };
});

mod.controller("DriveStorageLicenseController", function($http, $location,
                                                         AlertChannelService,
                                                         CurrentDomainService) {
  var self = this;

  self.submit = function() {
    $http.post("/api/assignDriveLicense", {
      domain: CurrentDomainService.get()
    }).success(function(data, status, headers, config) {
        $location.path("/done");
      }).error(function(data, status, headers, config) {
        AlertChannelService.Alert("Error assigning Drive Storage License: " + data.message);
      });
  };
});

mod.controller("UserCreateConfirmController", function($location, $http,
                                                       AlertChannelService,
                                                       CurrentDomainService) {
  var self = this;
  self.userStatus = -1;

  self.createUser = function() {
    $http.post("/api/createUser", {
      domain: CurrentDomainService.get()
    }).success(function(data, status, headers, config) {
        self.userStatus = 1;
        self.username = data.username;
        self.password = data.password;
      }).error(function(data, status, headers, config) {
        self.userStatus = 0;
        AlertChannelService.Alert("Error when creating user: " + data.message);
      });
  };

  self.next = function() {
    $location.path("/step6");
  };

  // Create a user as the controller loads.
  self.createUser();
});