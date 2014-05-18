var SiteVerificationConfirmController =
  function($location, SiteVerificationTokenCacheService) {
    var self = this;
    self.$location = $location;
    self.$siteVerificationTokenCacheService = SiteVerificationTokenCacheService;

    self.verificationInfo = SiteVerificationTokenCacheService.getData();
  };

/**
 * Proceed to the next step of the process.
 */
SiteVerificationConfirmController.prototype.next = function() {
  this.$location.path('/step4');
};

angular.module(CONTROLLERS).controller('SiteVerificationConfirmController',
  SiteVerificationConfirmController);
