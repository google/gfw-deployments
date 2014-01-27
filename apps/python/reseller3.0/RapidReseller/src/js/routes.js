var mod = angular.module(_APP_);

mod.config([
    '$routeProvider',
    '$locationProvider',
    '$httpProvider',
    function ($routeProvider, $locationProvider, $httpProvider) {

        $httpProvider.interceptors.push('loadingInterceptor');
        // Define routes here.
        $locationProvider.html5Mode(true);
        $routeProvider
            .when('/', {
                templateUrl: 'partials/index.html',
                controller: 'HomeController'
            })
            .when('/step1', {
                templateUrl: 'partials/customer.html',
                controller: 'CustomerController'
            })
            .when('/step2', {
                templateUrl: 'partials/subscription.html',
                controller: 'SubscriptionController'
            })
            .when("/step3", {
                templateUrl: 'partials/site_validation.html',
                controller: 'SiteVerificationController'
            })
            .when("/step3_confirm", {
                templateUrl: 'partials/site_validation_confirm.html',
                controller: 'SiteVerificationConfirmController'
            })
            .when('/step4', {
                templateUrl: 'partials/site_verification_action.html',
                controller: 'SiteVerificationActionController'
            })
            .when("/step5", {
                templateUrl: 'partials/user_create.html',
                controller: 'UserCreateController'
            })
            .when("/step5_confirm", {
                templateUrl: 'partials/user_create_confirm.html',
                controller: 'UserCreateConfirmController'
            })
            .when("/step6", {
                templateUrl: 'partials/drive_storage_create.html',
                controller: 'DriveStorageSubscriptionController'
            })
            .when("/step7", {
                templateUrl: 'partials/drive_storage_assign.html',
                controller: 'DriveStorageLicenseController'
            })
            .when("/done", {
                templateUrl: 'partials/done.html',
                controller: 'DoneController'
            })
            .otherwise({ redirectTo: '/' });
    }
]);