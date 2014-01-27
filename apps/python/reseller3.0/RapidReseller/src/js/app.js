var _APP_ = 'rapidreseller';
var _CONTROLLERS_ = _APP_ + '.controllers';
var _DIRECTIVES_ = _APP_ + '.directives';
var _FILTERS_ = _APP_ + '.filters';
var _SERVICES_ = _APP_ + '.services';

angular.module(_APP_, [
    _CONTROLLERS_,
    _DIRECTIVES_,
    _FILTERS_,
    _SERVICES_,
    'ngRoute'
]);

angular.module(_CONTROLLERS_, []);
angular.module(_DIRECTIVES_, []);
angular.module(_FILTERS_, []);
angular.module(_SERVICES_, []);

angular.element(document).ready(function () {
    angular.bootstrap(document, [_APP_]);
});
