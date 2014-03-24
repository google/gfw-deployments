describe('AlertChannelService', function() {
  var _service;
  var _rootScope;

  beforeEach(module(SERVICES));

  beforeEach(inject(function(AlertChannelService, $rootScope) {
    _service = AlertChannelService;
    _rootScope = $rootScope;
    spyOn(_rootScope, '$emit').andCallThrough();
    spyOn(_rootScope, '$on').andCallThrough();
  }));

  it('should dispatch an alert on the rootScope', function() {
    _service.Alert('HiMom!');
    expect(_rootScope.$emit).toHaveBeenCalled();
  });

  it('should provide a method to subscribe to alert broadcasts', function() {
    var _fired = false;
    var message = {};

    _service.onAlert(function(m) {
      _fired = true;
      message = m;
    });

    _service.Alert('HiMom!');

    expect(_fired).toBeTruthy();
    expect(_rootScope.$on).toHaveBeenCalled();
    expect(message.text).toBe('HiMom!');
    expect(message.type).toBe(_service.DEFAULT_ALERT_TYPE);
  });
});
