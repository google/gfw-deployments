mod = angular.module(SERVICES);

mod.factory('AlertChannelService', function($rootScope) {
  this.ALERT_CHANNEL_SERVICE_MESSAGE = '$__AlertChannelService_Alert';
  this.DEFAULT_ALERT_TYPE = 'danger';

  this.Alert = function(text, type) {
    if (type === undefined) {
      type = this.DEFAULT_ALERT_TYPE;
    }
    $rootScope.$emit(this.ALERT_CHANNEL_SERVICE_MESSAGE, {
      'text': text,
      'type': type
    });
  };

  this.onAlert = function(handler) {
    $rootScope.$on(this.ALERT_CHANNEL_SERVICE_MESSAGE, function(e, message) {
      handler(message);
    });
  };

  return this;
});
