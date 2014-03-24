mod = angular.module(CONTROLLERS);

mod.controller('SubscriptionController', function ($rootScope,
                                                   $http,
                                                   $location,
                                                   AlertChannelService,
                                                   CurrentDomainService) {
    var self = this;

    self.numberOfSeats = 5;

    self.submit = function () {
        $http.post("/api/createSubscription", {
            numberOfSeats: self.numberOfSeats,
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
            $location.path("/step3");
        }).error(function (data, status, headers, config) {
            AlertChannelService.Alert(data.message);
        });
    };
});