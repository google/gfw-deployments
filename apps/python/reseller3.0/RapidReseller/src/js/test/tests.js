describe('Services', function () {
    var _mockScope;

    beforeEach(module(_SERVICES_, function ($provide) {
        _mockScope = {
            $emit: jasmine.createSpy('rootScope.$emit'),
            $on: jasmine.createSpy('rootScope.$on'),
            $watch: jasmine.createSpy('rootScope.$watch')
        };
        $provide.value("$rootScope", _mockScope);
    }));

    describe("AlertChannelService", function () {
        var _service;

        beforeEach(inject(function (AlertChannelService) {
            _service = AlertChannelService;
        }));

        it("should dispatch an alert on the rootScope", function () {
            _service.Alert("HiMom!");
            expect(_mockScope.$emit).toHaveBeenCalled();
        });

        it("should provide a method to subscribe to alert broadcasts", function () {

            var _fired = false;
            _service.onAlert(function (message) {
            });
            _service.Alert("HiMom!");

            expect(_mockScope.$on).toHaveBeenCalled();
        });

    });

    describe('SiteVerificationTokenCacheService', function () {
        var _service;
        var _location;

        beforeEach(inject(function (SiteVerificationTokenCacheService, $location) {
            _location = $location;
            _service = SiteVerificationTokenCacheService;
        }));

        it('should store and retrieve a value', function () {
            _service.setData("hello");
            _location.path("/moo");
            expect(_service.getData()).toEqual("hello");
        });

        it('should store and retrieve a value as the location changes', function () {
            _service.setData("hello");
            expect(_service.getData()).toEqual("hello");
        })
    });
});