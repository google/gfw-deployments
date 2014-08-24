var APP = 'rapidreseller';
var CONTROLLERS = APP + '.controllers';
var DIRECTIVES = APP + '.directives';
var FILTERS = APP + '.filters';
var SERVICES = APP + '.services';
var SETTINGS = APP + '.settings';

angular.module(APP, [
  CONTROLLERS,
  DIRECTIVES,
  FILTERS,
  SERVICES,
  SETTINGS,
  'ngRoute'
]);

angular.module(CONTROLLERS, []);
angular.module(DIRECTIVES, []);
angular.module(FILTERS, []);
angular.module(SERVICES, []);
angular.module(SETTINGS, []);
