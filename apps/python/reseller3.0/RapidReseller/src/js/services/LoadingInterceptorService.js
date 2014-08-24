var LoadingInterceptorService = function($q, HttpLoadingChannelService) {
  HttpLoadingChannelService.setState(-1);

  return {
    'response': function(response) {
      HttpLoadingChannelService.setState(-1);
      HttpLoadingChannelService.setRequestInflight(0);
      return response || $q.when(response);
    },
    'request': function(config) {
      HttpLoadingChannelService.setState(1);
      HttpLoadingChannelService.setRequestInflight(1);
      return config || $q.when(config);
    },
    'requestError': function(rejection) {
      HttpLoadingChannelService.setState(0);
      HttpLoadingChannelService.setRequestInflight(0);
      return $q.reject(rejection);
    },
    'responseError': function(rejection) {
      HttpLoadingChannelService.setState(0);
      HttpLoadingChannelService.setRequestInflight(0);
      return $q.reject(rejection);
    }
  };
}

angular.module(SERVICES).service('LoadingInterceptorService',
  LoadingInterceptorService);
