<?php
  require_once "app.php";
  require_once 'settings.php';
  require_once 'constants.php';

  // Require Google Libs.
  require_once 'Google/Client.php';
  require_once 'Google/Service/Reseller.php';
  require_once 'Google/Service/Directory.php';
  require_once 'Google/Service/SiteVerification.php';
  require_once 'Google/Service/Licensing.php';


  class GoogleClientHelper {

    function GetClient() {
      global $SETTINGS;
      $client = new Google_Client();
      $client->setApplicationName("RapidReseller-PHP");

      // Google_Auth_AssertionCredentials implements its own cache.
      $key = file_get_contents($SETTINGS['OAUTH2_PRIVATE_KEY']);
      $client->setAssertionCredentials(new Google_Auth_AssertionCredentials(
        $SETTINGS['OAUTH2_SERVICE_ACCOUNT_EMAIL'],
        $SETTINGS['OAUTH2_SCOPES'],
        $key,
        'notasecret',
        'http://oauth.net/grant_type/jwt/1.0/bearer',
        $SETTINGS['RESELLER_ADMIN']
      ));

      if($client->getAuth()->isAccessTokenExpired()) {
        $client->getAuth()->refreshTokenWithAssertion($cred);
      }
      return $client;
    }
  }


  class IndexHandler extends RequestHandler {

    function get() {
      include "templates/base.html";
    }
  }


  class StepOneHandler extends RequestHandler {
    function post() {
      $json_data = $this->json_data;

      $reseller = new Google_Service_Reseller(GoogleClientHelper::GetClient());
      try {
        $reseller->customers->get($json_data['domain']);
        throw new Exception("Customer Exists!!");
      } catch(Exception $e) {
        // Exception is good in this case.
      }

      $customer = new Google_Service_Reseller_Customer();
      $customer->setCustomerDomain($json_data['domain']);
      $customer->setAlternateEmail($json_data['alternateEmail']);
      $customer->setPhoneNumber($json_data['phoneNumber']);

      $address = new Google_Service_Reseller_Address();
      $address->setContactName($json_data['postalAddress.contactName']);
      $address->setOrganizationName($json_data['postalAddress.organizationName']);
      $address->setLocality($json_data['postalAddress.locality']);
      $address->setCountryCode($json_data['postalAddress.countryCode']);
      $address->setRegion($json_data['postalAddress.region']);
      $address->setPostalCode($json_data['postalAddress.postalCode']);
      $address->setAddressLine1($json_data['postalAddress.addressLine1']);
      $customer->setPostalAddress($address);

      $reseller->customers->insert($customer);
    }
  }


  class StepTwoHandler extends RequestHandler {
    function post() {
      $json_data = $this->json_data;

      $service = new Google_Service_Reseller(GoogleClientHelper::GetClient());

      $subscription = new Google_Service_Reseller_Subscription();
      $subscription->setCustomerId($json_data['domain']);
      $subscription->setSubscriptionId($json_data['domain'] . "-apps");
      $subscription->setSkuId(ResellerSKU::GoogleApps);
      $subscription->setPurchaseOrderId('G00gl39001');

      $plan = new Google_Service_Reseller_SubscriptionPlan();
      $plan->setPlanName(ResellerPlanName::FLEXIBLE);
      $subscription->setPlan($plan);

      $seats = new Google_Service_Reseller_Seats();
      $seats->setNumberOfSeats($json_data['numberOfSeats']);
      $seats->setMaximumNumberOfSeats($json_data['numberOfSeats']);
      $subscription->setSeats($seats);

      $renewalSettings = new Google_Service_Reseller_RenewalSettings();
      $renewalSettings->setRenewalType(ResellerRenewalType::PAY_AS_YOU_GO);
      $subscription->setRenewalSettings($renewalSettings);

      $service->subscriptions->insert($json_data['domain'], $subscription);
    }
  }

  class StepThreeHandler extends RequestHandler {
    function post() {
      $json_data = $this->json_data;

      $verification_type = $json_data['verificationType'];
      $identifier = $json_data['verificationIdentifier'];
      $verification_method = $json_data['verificationMethod'];

      $service = new Google_Service_SiteVerification(
        GoogleClientHelper::GetClient());

      $request = new Google_Service_SiteVerification_SiteVerificationWebResourceGettokenRequest();
      $request->setVerificationMethod($verification_method);

      $site = new Google_Service_SiteVerification_SiteVerificationWebResourceGettokenRequestSite();
      $site->setType($verification_type);
      $site->setIdentifier($identifier);
      $request->setSite($site);

      $response = $service->webResource->getToken($request);

      return array(
        'verificationToken'       => $response->getToken(),
        'verificationType'        => $verification_type,
        'verificationMethod'      => $verification_method,
        'verificationIdentifier'  => $identifier
      );

    }
  }

  class StepFourHandler extends RequestHandler {
    function post() {
      //pass
      $json_data = $this->json_data;

      $verification_type = $json_data['verificationType'];
      $verification_identifier = $json_data['verificationIdentifier'];
      $verification_method = $json_data['verificationMethod'];

      $service = new Google_Service_SiteVerification(
        GoogleClientHelper::GetClient());

      $request = new Google_Service_SiteVerification_SiteVerificationWebResourceResource();

      $site = new Google_Service_SiteVerification_SiteVerificationWebResourceResourceSite();
      $site->setType($verification_type);
      $site->setIdentifier($verification_identifier);
      $request->setSite($site);

      $service->webResource->insert($verification_method, $request);
    }
  }

  class StepFiveHandler extends RequestHandler {
    function post() {
      $json_data = $this->json_data;

      $domain = $json_data['domain'];
      $username = "admin@" . $domain;
      $password = "P@ssw0rd!!";

      $service = new Google_Service_Directory(GoogleClientHelper::GetClient());

      $user = new Google_Service_Directory_User();
      $user->setPrimaryEmail($username);
      $user->setSuspended(false);
      $user->setPassword($password);

      $name = new Google_Service_Directory_UserName();
      $name->setGivenName("Admin");
      $name->setFamilyName("Admin");
      $name->setFullName("Admin Admin");
      $user->setName($name);

      $service->users->insert($user);

      $makeAdmin = new Google_Service_Directory_UserMakeAdmin();
      $makeAdmin->setStatus(true);
      $service->users->makeAdmin($username, $makeAdmin);

      return array(
        'domain'    => $domain,
        'username'  => $username,
        'password'  => $password
      );
    }
  }

  class StepSixHandler extends RequestHandler {
    function post() {
      $json_data = $this->json_data;

      $service = new Google_Service_Reseller(GoogleClientHelper::GetClient());

      $subscription = new Google_Service_Reseller_Subscription();
      $subscription->setCustomerId($json_data['domain']);
      $subscription->setSubscriptionId($json_data['domain'] . "-d20");
      $subscription->setSkuId(ResellerSKU::GoogleDriveStorage20GB);
      $subscription->setPurchaseOrderId('G00gl39001');

      $plan = new Google_Service_Reseller_SubscriptionPlan();
      $plan->setPlanName(ResellerPlanName::FLEXIBLE);
      $subscription->setPlan($plan);

      $seats = new Google_Service_Reseller_Seats();
      $seats->setNumberOfSeats(1);
      $seats->setMaximumNumberOfSeats(1);
      $subscription->setSeats($seats);

      $renewalSettings = new Google_Service_Reseller_RenewalSettings();
      $renewalSettings->setRenewalType(ResellerRenewalType::PAY_AS_YOU_GO);
      $subscription->setRenewalSettings($renewalSettings);

      $service->subscriptions->insert($json_data['domain'], $subscription);
    }
  }

  class StepSevenHandler extends RequestHandler {
    function post() {
      $json_data = $this->json_data;

      $service = new Google_Service_Licensing(GoogleClientHelper::GetClient());

      $request = new Google_Service_Licensing_LicenseAssignmentInsert();
      $request->setUserId('admin@' . $json_data['domain']);

      $service->licenseAssignments->insert(
        ResellerProduct::GoogleDrive,
        ResellerSKU::GoogleDriveStorage20GB,
        $request);
    }
  }

?>