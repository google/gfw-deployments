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

      $customer = new Google_Service_Reseller_Customer(array(
        'customerDomain' => $json_data['domain'],
        'alternateEmail' => $json_data['alternateEmail'],
        'phoneNumber' => $json_data['phoneNumber'],
        'postalAddress' => array(
          'contactName' => $json_data['postalAddress.contactName'],
          'organizationName' => $json_data['postalAddress.organizationName'],
          'locality' => $json_data['postalAddress.locality'],
          'countryCode'=> $json_data['postalAddress.countryCode'],
          'region' => $json_data['postalAddress.region'],
          'postalCode' => $json_data['postalAddress.postalCode'],
          'addressLine1' => $json_data['postalAddress.addressLine1']
        )
      ));

      $reseller->customers->insert($customer);

    }
  }


  class StepTwoHandler extends RequestHandler {
    function post() {
      $json_data = $this->json_data;

      $service = new Google_Service_Reseller(GoogleClientHelper::GetClient());

      $subscription = new Google_Service_Reseller_Subscription(array(
        'customerId' => $json_data['domain'],
        'skuId' => ResellerSKU::GoogleAppsForBusiness,
        'purchaseOrderId' => 'G00gle-9001',
        'plan' => array(
          'planName' => ResellerPlanName::FLEXIBLE
        ),
        'seats' => array(
          'numberOfSeats' => $json_data['numberOfSeats'],
          'maximumNumberOfSeats' => $json_data['numberOfSeats']
        ),
        'renewalSettings' => array(
          'renewalType' => ResellerRenewalType::PAY_AS_YOU_GO
        )
      ));

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

      $request = new Google_Service_SiteVerification_SiteVerificationWebResourceGettokenRequest(array(
        'verificationMethod' => $verification_method,
        'site' => array(
          'type' => $verification_type,
          'identifier' => $identifier
        )
      ));

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
      $json_data = $this->json_data;

      $verification_type = $json_data['verificationType'];
      $verification_identifier = $json_data['verificationIdentifier'];
      $verification_method = $json_data['verificationMethod'];

      $service = new Google_Service_SiteVerification(
        GoogleClientHelper::GetClient());

      $request = new Google_Service_SiteVerification_SiteVerificationWebResourceResource(array(
        'site' => array(
          'type' => $verification_type,
          'identifier' => $verification_identifier
        )
      ));

      $service->webResource->insert($verification_method, $request);
    }
  }

  class StepFiveHandler extends RequestHandler {
    function post() {
      $json_data = $this->json_data;

      $domain = $json_data['domain'];
      $primaryEmail = "admin@" . $domain;
      $password = "P@ssw0rd!!";

      $service = new Google_Service_Directory(GoogleClientHelper::GetClient());

      $user = new Google_Service_Directory_User(array(
        'primaryEmail' => $primaryEmail,
        'suspended' => FALSE,
        'password' => $password,
        'name' => array(
          'givenName' =>'Admin',
          'familyName' => 'Admin',
          'fullName' => 'Admin Admin'
        )
      ));

      $service->users->insert($user);

      $makeAdmin = new Google_Service_Directory_UserMakeAdmin(array(
        'status' => TRUE
      ));
      $service->users->makeAdmin($primaryEmail, $makeAdmin);

      return array(
        'domain'    => $domain,
        'username'  => $username,
        'password'  => $password
      );
    }
  }
?>