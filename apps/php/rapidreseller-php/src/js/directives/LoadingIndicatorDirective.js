var loadingIndicatorDirective = function() {
  return {
    restrict: 'E',
    transclude: true,
    scope: {},
    templateUrl: 'partials/_loading.html',
    controller: function($scope, HttpLoadingChannelService) {
      $scope.currentState = -1;
      HttpLoadingChannelService.onState(function(state) {
        $scope.currentState = state;
      });
    }
  };
};

angular.module(DIRECTIVES).directive('loadingIndicator',
  loadingIndicatorDirective);