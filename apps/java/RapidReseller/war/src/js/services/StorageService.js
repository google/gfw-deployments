mod = angular.module(SERVICES);

mod.factory('StorageService', function($window) {
  var _engine = $window.sessionStorage;
  //var _engine = $window.localStorage;
  var _prefix = APP + '#ng_';

  this.set = function(key, data) {
    _engine.setItem(_prefix + key, angular.toJson(data));
  };

  this.get = function(key) {
    data = _engine.getItem(_prefix + key);
    return angular.fromJson(data);
  };

  return this;
});
