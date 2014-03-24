var APP = 'rapidreseller';
var CONTROLLERS = APP + '.controllers';
var DIRECTIVES = APP + '.directives';
var FILTERS = APP + '.filters';
var SERVICES = APP + '.services';

angular.module(APP, [
  CONTROLLERS,
  DIRECTIVES,
  FILTERS,
  SERVICES,
  'ngRoute'
]);

angular.module(CONTROLLERS, []);
angular.module(DIRECTIVES, []);
angular.module(FILTERS, []);
angular.module(SERVICES, []);
