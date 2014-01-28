mod = angular.module(_DIRECTIVES_);

mod.directive("loadingIndicator", function () {
    return {
        restrict: 'E',
        transclude: true,
        scope: {},
        templateUrl: 'partials/_loading.html',
        controller: function ($scope, HttpLoadingChannelService) {
            $scope.currentState = -1;
            HttpLoadingChannelService.onState(function (state) {
                $scope.currentState = state;
            });
        }
    };
});

mod.directive('alertNotice', function () {
    return {
        restrict: 'E',
        transclude: true,
        scope: {},
        templateUrl: 'partials/_alerts.html',
        controller: function ($scope, AlertChannelService, $timeout) {
            $scope.alerts = [];

            AlertChannelService.onAlert(function (message) {
                $scope.alerts.push(message);
                $timeout(function () {
                    $scope.alerts.pop();
                }, 5000);
            });
        }
    };
});