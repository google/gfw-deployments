var CurrentDomainService = function(StorageService) {
  this._key = '$__CurrentDomainService';
  this.$storageService = StorageService;
};

CurrentDomainService.prototype.set = function(data) {
  this.$storageService.set(this._key, data);
};

CurrentDomainService.prototype.get = function() {
  return this.$storageService.get(this._key);
};

angular.module(SERVICES).service('CurrentDomainService', CurrentDomainService);
