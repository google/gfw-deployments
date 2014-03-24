mod = angular.module(SERVICES);

mod.factory('HttpLoadingChannelService', function($rootScope) {
  var HTTP_LOADING_CHANNEL_SERVICE_MESSAGE = '$__HttpLoadingChannelService';

  $rootScope.__CURRENT_HTTP_STATE = -1;

  this.setState = function(state) {
    $rootScope.$emit(HTTP_LOADING_CHANNEL_SERVICE_MESSAGE, state);
    $rootScope.__CURRENT_HTTP_STATE = state;
  };

  this.onState = function(handler) {
    $rootScope.$on(HTTP_LOADING_CHANNEL_SERVICE_MESSAGE, function(e, message) {
      handler(message);
    });
  };

  return this;
});
