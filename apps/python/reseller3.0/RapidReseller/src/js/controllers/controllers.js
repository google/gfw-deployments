mod = angular.module(CONTROLLERS);

mod.controller('CustomerController', function ($http,
                                               $location,
                                               AlertChannelService,
                                               CurrentDomainService) {

    var self = this;
    // Set a sensible default domain.
    self.customerDomain = "demo-"+new Date().getTime()+".resold.richieforeman.net";
    self.alternateEmail = "nobody@google.com";
    self.phoneNumber = "212.565.0000";
    self.contactName = "A Googler";
    self.organizationName = "Google Demo Company";
    self.locality = "NYC";
    self.region = "NY";
    self.countryCode = "US";
    self.postalCode = "11101";
    self.addressLine1 = "76 9th Ave";

    self.submit = function() {
        $http.post("/api/createCustomer", {
            'domain': this.customerDomain,
            'alternateEmail': this.alternateEmail,
            'phoneNumber': this.phoneNumber,
            'postalAddress.contactName': this.contactName,
            'postalAddress.addressLine1': this.addressLine1,
            'postalAddress.organizationName': this.organizationName,
            'postalAddress.locality': this.locality,
            'postalAddress.region': this.region,
            'postalAddress.countryCode': this.countryCode,
            'postalAddress.postalCode': this.postalCode
        }).success(function (data, status, headers, config) {
            CurrentDomainService.set(self.customerDomain);
            $location.path("/step2");
        }).error(function(data, status, headers, config) {
            AlertChannelService.Alert(data.message);
        });
    };
});

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

mod.controller("SiteVerificationConfirmController", function($location,
                                                             SiteVerificationTokenCacheService) {

    var self = this;

    self.verificationInfo = SiteVerificationTokenCacheService.getData();

    self.next = function() {
        $location.path("/step4");
    };

});

mod.controller("UserCreateController", function($location) {
    var self = this;
    self.next = function() {
        $location.path("/step5_confirm");
    };
});

mod.controller("DriveStorageSubscriptionController", function($http,
                                                              $location,
                                                              AlertChannelService,
                                                              CurrentDomainService) {
    var self = this;

    self.submit = function () {
        $http.post("/api/createDriveStorageSubscription", {
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
            $location.path("/step7");
        }).error(function (data, status, headers, config) {
            AlertChannelService.Alert("Error creating Drive Storage Subscription: " + data.message);
        });
    };
});

mod.controller("DriveStorageLicenseController", function ($http,
                                                          $location,
                                                          AlertChannelService,
                                                          CurrentDomainService) {
    var self = this;

    self.submit = function () {
        $http.post("/api/assignDriveLicense", {
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
            $location.path("/done");
        }).error(function (data, status, headers, config) {
            AlertChannelService.Alert("Error assigning Drive Storage License: " + data.message);
        });
    };
});

mod.controller("UserCreateConfirmController", function($location,
                                                       $http,
                                                       AlertChannelService,
                                                       CurrentDomainService) {
    var self = this;
    self.userStatus = -1;

    self.createUser = function () {
        $http.post("/api/createUser", {
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
            self.userStatus = 1;
            self.username = data.username;
            self.password = data.password;
        }).error(function (data, status, headers, config) {
            self.userStatus = 0;
            AlertChannelService.Alert("Error when creating user: " + data.message);
        });
    };

    self.next = function() {
        $location.path("/step6");
    };

    // Create a user as the controller loads.
    self.createUser();
});


mod.controller("SiteVerificationActionController", function($http,
                                                            $location,
                                                            SiteVerificationTokenCacheService,
                                                            CurrentDomainService) {
    var self = this;

    var verificationInfo = SiteVerificationTokenCacheService.getData();

    var STATUS = {
        WORKING: -1,
        OK: 1,
        FAILED: 0
    };

    self.next = function() {
        $location.path("/step5");
    };

    self.doVerification = function() {
        self.verificationStatus = STATUS.WORKING;
        $http.post("/api/testValidation", {
            verification_type: verificationInfo.verification_type,
            verification_identifier: verificationInfo.verification_identifier,
            verification_method: verificationInfo.verification_method,
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
           self.verificationStatus = STATUS.OK;
        }).error(function(data, status, headers, config) {
            self.verificationStatus = STATUS.FAILED;
        });
    };

    // attempt verification as the controller loads...
    self.doVerification();

});

mod.controller('SiteVerificationController', function ($scope,
                                                       $rootScope,
                                                       $http,
                                                       $location,
                                                       AlertChannelService,
                                                       SiteVerificationTokenCacheService,
                                                       CurrentDomainService) {
    var self = this;

    // Display all of the options
    self.verificationMethods = [
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
    self.verificationMethod = self.verificationMethods[0];

    // listen for changes to the verificationMethod and regen the identifier.
    $scope.$watch('verificationMethod', function () {
        var prefix = self.verificationMethod.prefix;
        self.verificationIdentifier = prefix + CurrentDomainService.get();
    });

    self.submit = function() {
        $http.post("/api/getSiteValidationToken", {
            verificationMethod: self.verificationMethod.value,
            verificationType: self.verificationMethod.type,
            verificationIdentifier: self.verificationIdentifier,
            domain: CurrentDomainService.get()
        }).success(function (data, status, headers, config) {
            SiteVerificationTokenCacheService.setData(data);
            $location.path("/step3_confirm");
        }).error(function (data, status, headers, config) {
            AlertChannelService.Alert(data.message);
        });
    };
});