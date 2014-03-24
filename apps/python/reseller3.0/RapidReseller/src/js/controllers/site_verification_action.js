mod = angular.module(CONTROLLERS);

mod.controller('SiteVerificationActionController', function($http, $location, SiteVerificationTokenCacheService, CurrentDomainService) {
  var self = this;

  var verificationInfo = SiteVerificationTokenCacheService.getData();

  var STATUS = {
    WORKING: -1,
    OK: 1,
    FAILED: 0
  };

  self.next = function() {
    $location.path('/step5');
  };

  self.doVerification = function() {
    self.verificationStatus = STATUS.WORKING;

    $http.post('/api/testValidation', {
      verificationType: verificationInfo.verificationType,
      verificationIdentifier: verificationInfo.verificationIdentifier,
      verificationMethod: verificationInfo.verificationMethod,
      domain: CurrentDomainService.get()
    }).success(function(data, status, headers, config) {
      self.verificationStatus = STATUS.OK;
    }).error(function(data, status, headers, config) {
      self.verificationStatus = STATUS.FAILED;
    });
  };

  // attempt verification as the controller loads...
  self.doVerification();
});
