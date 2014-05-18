describe('LoadingInterceptorService', function() {
  var _service;
  var _rootScope;
  var _loadingService;
  var stateSpy;

  beforeEach(module(SERVICES));

  beforeEach(inject(function(LoadingInterceptorService, $rootScope,
                             HttpLoadingChannelService) {
    _rootScope = $rootScope;
    _loadingService = HttpLoadingChannelService;
    stateSpy = spyOn(HttpLoadingChannelService, 'setState');

    _service = LoadingInterceptorService;

  }));

  it('should return 4 methods', function() {
    expect(_service.request).toBeDefined();
    expect(_service.requestError).toBeDefined();
    expect(_service.response).toBeDefined();
    expect(_service.responseError).toBeDefined();
  });

  it('should set the global state when the request starts', function() {
    _service.request({});
    expect(stateSpy).toHaveBeenCalledWith(1);
  });

  it('should set the global state when the request errors', function() {
    _service.requestError({});
    expect(stateSpy).toHaveBeenCalledWith(0);
  });

  it('should reset the global state when the request responds', function() {
    _service.response({});
    expect(stateSpy).toHaveBeenCalledWith(-1);
  });

  it('should set the global state when the response errors', function() {
    _service.responseError({});
    expect(stateSpy).toHaveBeenCalledWith(0);
  });

  it('Should set the initial request state', function() {
    expect(_rootScope.__CURRENT_HTTP_STATE).toBe(-1);
  });
});
