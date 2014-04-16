var SiteVerificationActionController = function($http, $location,
                                                SiteVerificationTokenCacheService,
                                                CurrentDomainService) {
  var self = this;

  self.$http = $http;
  self.$location = $location;
  self.$siteVerificationTokenCacheService = SiteVerificationTokenCacheService;
  self.$currentDomainService = CurrentDomainService;


  self.verificationInfo = SiteVerificationTokenCacheService.getData();

  // attempt to do verification as the controller loads.
  self.doVerification();
};

SiteVerificationActionController.prototype.next = function() {
  this.$location.path('/step5');
};

SiteVerificationActionController.prototype.doVerification = function() {
  var self = this;

  var STATUS = {
    WORKING: -1,
    OK: 1,
    FAILED: 0
  };

  self.verificationStatus = STATUS.WORKING;

  self.$http.post('/api/testValidation', {
    verificationType: self.verificationInfo.verificationType,
    verificationIdentifier: self.verificationInfo.verificationIdentifier,
    verificationMethod: self.verificationInfo.verificationMethod,
    domain: self.$currentDomainService.get()
  }).success(function(data, status, headers, config) {
      self.verificationStatus = STATUS.OK;
  }).error(function(data, status, headers, config) {
      self.verificationStatus = STATUS.FAILED;
  });
};

angular.module(CONTROLLERS).controller('SiteVerificationActionController',
  SiteVerificationActionController);
