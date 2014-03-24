mod = angular.module(SERVICES);
mod.factory('CurrentDomainService', function(StorageService) {
  var _key = 'CurrentDomainService';

  this.set = function(data) {
    StorageService.set(_key, data);
  };

  this.get = function(data) {
    return StorageService.get(_key);
  };

  return this;
});
