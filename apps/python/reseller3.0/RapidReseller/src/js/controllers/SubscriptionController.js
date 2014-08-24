var SubscriptionController = function($rootScope, $http, $location,
                                      AlertChannelService,
                                      CurrentDomainService,
                                      SETTINGS) {
  this.numberOfSeats = 5;

  this.gabSkuIds = SETTINGS.GAB_SKU_IDS;
  this.skuId = this.gabSkuIds[SETTINGS.GAB_SKU_DEFAULT_INDEX];

  this.planNameOptions = SETTINGS.PLAN_NAME_OPTIONS;
  this.planName = this.planNameOptions[SETTINGS.PLAN_NAME_DEFAULT_INDEX];

  this.renewalTypeOptions = SETTINGS.RENEWAL_TYPE_OPTIONS;
  this.renewalType = this.renewalTypeOptions[SETTINGS.RENEWAL_TYPE_DEFAULT_INDEX];

  this.purchaseOrderId = "credit_card_transaction:29374283496238946";

  this.$http = $http;
  this.$location = $location;
  this.$settings = SETTINGS;
  this.$alertChannelService = AlertChannelService;
  this.$currentDomainService = CurrentDomainService;
};

SubscriptionController.prototype.submit = function() {
  var self = this;
  self.$http.post(this.$settings.CREATE_SUBSCRIPTION_ENDPOINT, {
    numberOfSeats: self.numberOfSeats,
    domain: self.$currentDomainService.get(),
    skuId: self.skuId.value,
    planName: self.planName.value,
    renewalType: self.renewalType.value,
    purchaseOrderId: self.purchaseOrderId
  }).success(function(data, status, headers, config) {
      self.$location.path("/step3");
  }).error(function(data, status, headers, config) {
      self.$alertChannelService.Alert(data.message);
  });
};

angular.module(CONTROLLERS).controller('SubscriptionController',
  SubscriptionController);