var AlertChannelService = function($rootScope) {
  this.ALERT_CHANNEL_SERVICE_MESSAGE = '$__AlertChannelService_Alert';
  this.DEFAULT_ALERT_TYPE = 'danger';
  this.$$scope = $rootScope;
};

/**
 * Dispatch a message that appears as a notification bar at the top
 * of the application.
 *
 * @param {!string} text Alert Text
 * @param {!string} type Alert Type (corresponds to bootstrap classes)
 */
AlertChannelService.prototype.Alert = function(text, type) {
  if (type === undefined) {
    type = this.DEFAULT_ALERT_TYPE;
  }
  this.$$scope.$emit(this.ALERT_CHANNEL_SERVICE_MESSAGE, {
    'text': text,
    'type': type
  });
};

/**
 * Alert Callback
 * @param {!function} handler Event handler to dispatch
 */
AlertChannelService.prototype.onAlert = function(handler) {
  this.$$scope.$on(this.ALERT_CHANNEL_SERVICE_MESSAGE, function(e, message) {
    handler(message);
  });
};

angular.module(SERVICES).service('AlertChannelService', AlertChannelService);
