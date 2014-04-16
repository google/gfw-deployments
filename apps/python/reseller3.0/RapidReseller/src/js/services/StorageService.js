var StorageService = function($window) {
  this.$storage = $window.sessionStorage;
  this._prefix = APP + '#ng_';

  this.$toJson = angular.toJson;
  this.$fromJson = angular.fromJson;
}

StorageService.prototype._getKey = function(key) {
  return this._prefix + key;
};

StorageService.prototype.set = function(key, data) {
  this.$storage.setItem(this._getKey(key), this.$toJson(data));
};

StorageService.prototype.get = function(key) {
  var data = this.$storage.getItem(this._getKey(key));
  return this.$fromJson(data);
};

angular.module(SERVICES).service('StorageService', StorageService);
