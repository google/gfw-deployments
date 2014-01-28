mod = angular.module(_CONTROLLERS_);

mod.controller('HomeController', function ($scope, $http) {
    // Nothing here, move along.
});

mod.controller("DoneController", function($scope) {
    // Nothing here, move along.
});

mod.controller('CustomerController', function ($scope,
                                               $http,
                                               $location,
                                               AlertChannelService,
                                               CurrentDomainService) {
    // Set a sensible default domain.
    $scope.customerDomain = "demo-"+new Date().getTime()+".resold.richieforeman.net";
    $scope.alternateEmail = "nobody@google.com";
    $scope.phoneNumber = "212.565.0000";
    $scope.contactName = "A Googler";
    $scope.organizationName = "Google Demo Company";
    $scope.locality = "NYC";
    $scope.region = "NY";
    $scope.countryCode = "US";
    $scope.postalCode = "11101";
    $scope.addressLine1 = "76 9th Ave";

    $scope.submit = function() {
        $http.post("/api/createCustomer", {
            'domain': $scope.customerDomain,
            'alternateEmail': $scope.alternateEmail,
            'phoneNumber': $scope.phoneNumber,
            'postalAddress.contactName': $scope.contactName,
            'postalAddress.addressLine1': $scope.addressLine1,
            'postalAddress.organizationName': $scope.organizationName,
            'postalAddress.locality': $scope.locality,
            'postalAddress.region': $scope.region,
            'postalAddress.countryCode': $scope.countryCode,
            'postalAddress.postalCode': $scope.postalCode
        }).success(function (data, status, headers, config) {
            CurrentDomainService.set($scope.domain);
            $location.path("/step2");
        }).error(function(data, status, headers, config) {
            AlertChannelService.Alert(data.message);
        });
    };
});

mod.controller('SubscriptionController', function ($scope,
                                                   $rootScope,
                                                   $http,
                                                   $location,
                                                   AlertChannelService,
                                                   CurrentDomainService) {

    $scope.numberOfSeats = 5;

    $scope.submit = function () {
        $http.post("/api/createSubscription", {
            numberOfSeats: $scope.numberOfSeats,
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
            $location.path("/step3");
        }).error(function (data, status, headers, config) {
            AlertChannelService.Alert(data.message);
        });
    };
});

mod.controller("SiteVerificationConfirmController", function($scope,
                                                             $http,
                                                             $location,
                                                             SiteVerificationTokenCacheService) {

    var verificationInfo = SiteVerificationTokenCacheService.getData();
    $scope.verificationInfo = verificationInfo;

    $scope.next = function() {
        $location.path("/step4");
    };

});

mod.controller("UserCreateController", function($scope, $location) {
    $scope.next = function() {
        $location.path("/step5_confirm");
    };
});

mod.controller("DriveStorageSubscriptionController", function($scope,
                                                              $http,
                                                              $location,
                                                              AlertChannelService,
                                                              CurrentDomainService) {
    $scope.submit = function () {
        $http.post("/api/createDriveStorageSubscription", {
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
            $location.path("/step7");
        }).error(function (data, status, headers, config) {
            AlertChannelService.Alert("Error creating Drive Storage Subscription: " + data.message);
        });
    };
});

mod.controller("DriveStorageLicenseController", function ($scope,
                                                          $http,
                                                          $location,
                                                          AlertChannelService,
                                                          CurrentDomainService) {
    $scope.submit = function () {
        $http.post("/api/assignDriveLicense", {
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
            $location.path("/done");
        }).error(function (data, status, headers, config) {
            AlertChannelService.Alert("Error assigning Drive Storage License: " + data.message);
        });
    };
});

mod.controller("UserCreateConfirmController", function($scope,
                                                       $location,
                                                       $http,
                                                       AlertChannelService,
                                                       CurrentDomainService) {
    $scope.userStatus = -1;

    $http.post("/api/createUser", {
        domain: CurrentDomainService.get()
    }).success(function (data, status, headers, config) {
        $scope.userStatus = 1;
        $scope.username = data.username;
        $scope.password = data.password;
    }).error(function (data, status, headers, config) {
        $scope.userStatus = 0;
        AlertChannelService.Alert("Error when creating user: " + data.message);
    });

    $scope.next = function() {
        $location.path("/step6");
    };
});


mod.controller("SiteVerificationActionController", function($scope,
                                                            $http,
                                                            $location,
                                                            SiteVerificationTokenCacheService,
                                                            CurrentDomainService) {

    var verificationInfo = SiteVerificationTokenCacheService.getData();

    var STATUS = {
        WORKING: -1,
        OK: 1,
        FAILED: 0
    };

    $scope.next = function() {
        $location.path("/step5");
    };

    $scope.doVerification = function() {
        $scope.verificationStatus = STATUS.WORKING;
        $http.post("/api/testValidation", {
            verification_type: verificationInfo.verification_type,
            verification_identifier: verificationInfo.verification_identifier,
            verification_method: verificationInfo.verification_method,
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
           $scope.verificationStatus = STATUS.OK;
        }).error(function(data, status, headers, config) {
            $scope.verificationStatus = STATUS.FAILED;
        });
    };

    // attempt verification as the controller loads...
    $scope.doVerification();

});

mod.controller('SiteVerificationController', function ($scope,
                                                       $rootScope,
                                                       $http,
                                                       $location,
                                                       AlertChannelService,
                                                       SiteVerificationTokenCacheService,
                                                       CurrentDomainService) {

    // Display all of the options
    $scope.verificationMethods = [
        {
            value: "FILE",
            type: "SITE",
            label: "FILE - Upload a file with a specific name to the website.",
            prefix: "http://"

        },
        {
            value: "META",
            type: "SITE",
            label: "META - Place a tag in the meta section of the website.",
            prefix: "http://"
        },
        {
            value: "ANALYTICS",
            type: "SITE",
            label: "ANALYTICS - Validate using an existing Google Analytics domain.",
            prefix: "http://"
        },
        {
            value: "TAG_MANAGER",
            type: "SITE",
            label: "TAG_MANAGER - Not sure what this one does.",
            prefix: "http://"
        },
        {
            value: "DNS_TXT",
            type: "INET_DOMAIN",
            label: "DNS_TXT - Using a DNS Text Record",
            prefix: ""
        },
        {
            value: "DNS_CNAME",
            type: "INET_DOMAIN",
            label: "DNS_CNAME - Using a DNS CNAME Record",
            prefix: ""
        }
    ];

    // Set a sensible default.
    $scope.verificationMethod = $scope.verificationMethods[0];

    // listen for changes to the verificationMethod and regen the identifier.
    $scope.$watch('verificationMethod', function () {
        $scope.verificationIdentifier = $scope.verificationMethod.prefix +
            CurrentDomainService.get();
    });

    $scope.submit = function() {
        $http.post("/api/getSiteValidationToken", {
            verificationMethod: $scope.verificationMethod.value,
            verificationType: $scope.verificationMethod.type,
            verificationIdentifier: $scope.verificationIdentifier,
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
            SiteVerificationTokenCacheService.setData(data);
            $location.path("/step3_confirm");
        }).error(function (data, status, headers, config) {
            AlertChannelService.Alert(data.message);
        });
    };
});