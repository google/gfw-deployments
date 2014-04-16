var SiteVerificationController = function($scope, $rootScope, $http, $location,
                                          AlertChannelService,
                                          SiteVerificationTokenCacheService,
                                          CurrentDomainService) {
  var self = this;
  self.$scope = $scope;
  self.$rootScope = $rootScope;
  self.$http = $http;
  self.$location = $location;
  self.$alertChannelService = AlertChannelService;
  self.$siteVerificationTokenCacheService = SiteVerificationTokenCacheService;
  self.$currentDomainService = CurrentDomainService;

  self.verificationMethods = [
    {
      value: 'FILE',
      type: 'SITE',
      label: 'FILE - Upload a file with a specific name to the website.',
      prefix: 'http://'

    },
    {
      value: 'META',
      type: 'SITE',
      label: 'META - Place a tag in the meta section of the website.',
      prefix: 'http://'
    },
    {
      value: 'ANALYTICS',
      type: 'SITE',
      label: 'ANALYTICS - Validate using an existing Google Analytics domain.',
      prefix: 'http://'
    },
    {
      value: 'TAG_MANAGER',
      type: 'SITE',
      label: 'TAG_MANAGER - Not sure what this one does.',
      prefix: 'http://'
    },
    {
      value: 'DNS_TXT',
      type: 'INET_DOMAIN',
      label: 'DNS_TXT - Using a DNS Text Record',
      prefix: ''
    },
    {
      value: 'DNS_CNAME',
      type: 'INET_DOMAIN',
      label: 'DNS_CNAME - Using a DNS CNAME Record',
      prefix: ''
    }
  ];

  // Set a sensible default.
  self.verificationMethod = self.verificationMethods[0];

  $scope.$watch(function() {
    return self.verificationMethod;
  }, function() {
    var prefix = self.verificationMethod.prefix;
    self.verificationIdentifier = prefix + CurrentDomainService.get();
  });
};

SiteVerificationController.prototype.submit = function() {
  var self = this;
  self.$http.post('/api/getSiteValidationToken', {
    verificationMethod: self.verificationMethod.value,
    verificationType: self.verificationMethod.type,
    verificationIdentifier: self.verificationIdentifier,
    domain: self.$currentDomainService.get()
  }).success(function(data, status, headers, config) {
    self.$siteVerificationTokenCacheService.setData(data);
    self.$location.path('/step3_confirm');
  }).error(function(data, status, headers, config) {
    self.$alertChannelService.Alert(data.message);
  });
};

angular.module(CONTROLLERS).controller('SiteVerificationController',
  SiteVerificationController);
