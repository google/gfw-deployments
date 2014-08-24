var SiteVerificationConfirmController =
  function($location, SiteVerificationTokenCacheService) {
    this.$location = $location;
    this.$siteVerificationTokenCacheService = SiteVerificationTokenCacheService;

    this.verificationInfo = SiteVerificationTokenCacheService.getData();
  };

/**
 * Proceed to the next step of the process.
 */
SiteVerificationConfirmController.prototype.next = function() {
  this.$location.path('/step4');
};

angular.module(CONTROLLERS).controller('SiteVerificationConfirmController',
  SiteVerificationConfirmController);
