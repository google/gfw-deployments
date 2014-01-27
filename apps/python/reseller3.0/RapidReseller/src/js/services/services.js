mod = angular.module(_SERVICES_);

mod.factory("StorageService", function ($window) {
    var _engine = $window.sessionStorage;
    //var _engine = $window.localStorage;
    var _prefix = _APP_ + "#ng_";

    this.set = function (key, data) {
        _engine.setItem(_prefix + key, angular.toJson(data));
    };

    this.get = function (key) {
        data = _engine.getItem(_prefix + key);
        return angular.fromJson(data);
    };

    return this;
});

mod.factory("CurrentDomainService", function (StorageService) {
    var _key = "CurrentDomainService";

    this.set = function (data) {
        StorageService.set(_key, data);
    };

    this.get = function (data) {
        return StorageService.get(_key);
    };

    return this;
});

mod.factory("SiteVerificationTokenCacheService", function (StorageService) {
    var _key = "SiteVerificationTokenCache";

    this.setData = function (data) {
        StorageService.set(_key, data);
    };

    this.getData = function () {
        return StorageService.get(_key);
    };

    return this;
});