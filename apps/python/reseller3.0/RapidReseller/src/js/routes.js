var mod = angular.module(APP);

mod.config([
  '$routeProvider',
  '$locationProvider',
  '$httpProvider',
  function($routeProvider, $locationProvider, $httpProvider) {

    $httpProvider.interceptors.push('LoadingInterceptorService');

    // Define routes here.
    $locationProvider.html5Mode(true);
    $routeProvider.when('/', {
      templateUrl: 'partials/index.html'
    }).when('/step1', {
      templateUrl: 'partials/customer.html',
      controller: 'CustomerController',
      controllerAs: 'customer'
    }).when('/step2', {
      templateUrl: 'partials/subscription.html',
      controller: 'SubscriptionController',
      controllerAs: 'subscription'
    }).when('/step3', {
      templateUrl: 'partials/site_verification.html',
      controller: 'SiteVerificationController',
      controllerAs: 'siteVerification'
    }).when('/step3_confirm', {
      templateUrl: 'partials/site_verification_confirm.html',
      controller: 'SiteVerificationConfirmController',
      controllerAs: 'siteVerificationConfirm'
    }).when('/step4', {
      templateUrl: 'partials/site_verification_action.html',
      controller: 'SiteVerificationActionController',
      controllerAs: 'siteVerificationAction'
    }).when('/step5', {
      templateUrl: 'partials/user_create.html',
      controller: 'UserCreateController',
      controllerAs: 'userCreate'
    }).when('/step5_confirm', {
      templateUrl: 'partials/user_create_confirm.html',
      controller: 'UserCreateConfirmController',
      controllerAs: 'userCreateConfirm'
    }).when('/step6', {
      templateUrl: 'partials/drive_storage_create.html',
      controller: 'DriveStorageSubscriptionController',
      controllerAs: 'driveStorageCreate'
    }).when('/step7', {
      templateUrl: 'partials/drive_storage_assign.html',
      controller: 'DriveStorageLicenseController',
      controllerAs: 'driveStorageAssign'
    }).when('/done', {
      templateUrl: 'partials/done.html'
    }).otherwise({ redirectTo: '/' });
  }
]);
