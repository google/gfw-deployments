var HttpLoadingChannelService = function($rootScope) {
  this.HTTP_LOADING_CHANNEL_SERVICE_MESSAGE = '$__HttpLoadingChannelService';
  this.$scope = $rootScope;

  $rootScope.__CURRENT_HTTP_STATE = -1;
};

HttpLoadingChannelService.prototype.setState = function(state) {
  this.$scope.$emit(this.HTTP_LOADING_CHANNEL_SERVICE_MESSAGE, state);
  this.$scope.__CURRENT_HTTP_STATE = state;
};

HttpLoadingChannelService.prototype.onState = function(handler) {
  this.$scope.$on(this.HTTP_LOADING_CHANNEL_SERVICE_MESSAGE, function(e, msg) {
    handler(msg);
  });
};

angular.module(SERVICES).service('HttpLoadingChannelService',
  HttpLoadingChannelService);
