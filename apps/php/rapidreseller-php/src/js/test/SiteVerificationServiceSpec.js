describe('SiteVerificationTokenCacheService', function() {
  var _service;
  var _location;

  beforeEach(module(SERVICES));

  beforeEach(inject(function(SiteVerificationTokenCacheService, $location) {
    _location = $location;
    _service = SiteVerificationTokenCacheService;
  }));

  it('should store and retrieve a value', function() {
    _service.setData('hello');
    expect(_service.getData()).toEqual('hello');
  });

  it('should store and retrieve a value as the location changes', function() {
    _service.setData('hello');
    _location.path('/moo');
    expect(_service.getData()).toEqual('hello');
  });
});
