mod = angular.module(DIRECTIVES);

mod.directive('alertNotice', function() {
  return {
    restrict: 'E',
    transclude: true,
    scope: {},
    templateUrl: 'partials/_alerts.html',
    controller: function($scope, AlertChannelService, $timeout) {
      $scope.alerts = [];

      AlertChannelService.onAlert(function(message) {
        $scope.alerts.push(message);
        $timeout(function() {
          $scope.alerts.pop();
        }, 5000);
      });
    }
  };
});