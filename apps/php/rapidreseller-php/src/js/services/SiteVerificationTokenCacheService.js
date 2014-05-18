var SiteVerificationTokenCacheService = function(StorageService) {
  this._KEY = 'SiteVerificationTokenCache';
  this.$storage = StorageService;
}

SiteVerificationTokenCacheService.prototype.setData = function(data) {
  this.$storage.set(this._KEY, data);
};

SiteVerificationTokenCacheService.prototype.getData = function(data) {
  return this.$storage.get(this._KEY);
};

angular.module(SERVICES).service('SiteVerificationTokenCacheService',
  SiteVerificationTokenCacheService);
