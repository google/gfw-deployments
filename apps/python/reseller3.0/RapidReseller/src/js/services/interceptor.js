mod = angular.module(SERVICES);

mod.factory("loadingInterceptor", function ($q, HttpLoadingChannelService) {

    // Broadcast an initial state.
    HttpLoadingChannelService.setState(-1);

    return {
        'request': function (config) {
            HttpLoadingChannelService.setState(1);
            return config || $q.when(config);
        },
        'requestError': function (rejection) {
            HttpLoadingChannelService.setState(0);
            return $q.reject(rejection);
        },
        'response': function (response) {
            HttpLoadingChannelService.setState(-1);
            return response || $q.when(response);
        },
        'responseError': function (rejection) {
            HttpLoadingChannelService.setState(0);
            return $q.reject(rejection);
        }
    };

});