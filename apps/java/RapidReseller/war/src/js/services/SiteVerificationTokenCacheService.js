mod = angular.module(SERVICES);
mod.factory('SiteVerificationTokenCacheService', function(StorageService) {
  var _key = 'SiteVerificationTokenCache';

  this.setData = function(data) {
    StorageService.set(_key, data);
  };

  this.getData = function() {
    return StorageService.get(_key);
  };

  return this;
});
