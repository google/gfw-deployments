mod = angular.module(_SERVICES_);

mod.factory("HttpLoadingChannelService", function ($rootScope) {
    var HTTP_LOADING_CHANNEL_SERVICE_MESSAGE = "$__HttpLoadingChannelService";

    this.setState = function (state) {
        $rootScope.$emit(HTTP_LOADING_CHANNEL_SERVICE_MESSAGE, state);
    };

    this.onState = function (handler) {
        $rootScope.$on(HTTP_LOADING_CHANNEL_SERVICE_MESSAGE, function (e, message) {
            handler(message);
        });
    }

    return this;
});

mod.factory("AlertChannelService", function ($rootScope) {
    var ALERT_CHANNEL_SERVICE_MESSAGE = "$__AlertChannelService_Alert";

    this.Alert = function (text, type) {
        if (type === undefined) {
            type = "danger";
        }
        $rootScope.$emit(ALERT_CHANNEL_SERVICE_MESSAGE, {
            'text': text,
            'type': type
        });
    };

    this.onAlert = function (handler) {
        $rootScope.$on(ALERT_CHANNEL_SERVICE_MESSAGE, function (event, message) {
            handler(message);
        });
    };

    return this;
});