<?
    /*

    DISCLAIMER:

    (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
    WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
    WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND

    (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
    OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
    DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
    GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
    THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR
    ITS DERIVATIVES.

    */
    require_once 'config.php';
    require_once 'google-api-php-client/src/Google_Client.php';
    require_once 'google-api-php-client/src/contrib/Google_ResellerService.php';
    require_once 'constants.php';

    // Build the client using some custom configuration values.
    $client = new Google_Client($GOOGLE_CLIENT_CONFIG);
    $client->setApplicationName("Rapid Reseller - Transfer Token Demo (PHP)");
    $client->setScopes($SETTINGS['OAUTH2_SCOPES']);

    // Authenticate the client.
    $client->setAssertionCredentials(new Google_AssertionCredentials(
        $SETTINGS['OAUTH2_SERVICE_ACCOUNT_EMAIL'],
        $SETTINGS['OAUTH2_SCOPES'],
        file_get_contents($SETTINGS['OAUTH2_PRIVATE_KEY']),
        'notasecret',
        'http://oauth.net/grant_type/jwt/1.0/bearer',
        $SETTINGS['RESELLER_ADMIN']
    ));

    // This is ugly, but the client ID must be set here.
    $client->setClientId($SETTINGS['OAUTH2_CLIENT_ID']);

    // A service object takes a constructed and authenticated client.
    $service = new Google_ResellerService($client);

    // Create a new subscription object.
    $subscription = new Google_Subscription();
    $subscription->setCustomerId($_POST['customerDomain']);
    $subscription->setSubscriptionId('123');
    $subscription->setSkuId(ResellerSKU::GoogleApps);
    $subscription->setPurchaseOrderId("mypurchaseorder-123");

    // Subscriptions have a plan.
    // Note: It is not possible to transfer a premier customer to a trial.
    $plan = new Google_SubscriptionPlan();
    $plan->setPlanName(ResellerPlanName::FLEXIBLE);
    $plan->setIsCommitmentPlan(FALSE);

    // Only annual subscription plans have a commitment interval.
    // The following lines are commented out for reference.

    /*
        $interval = new Google_SubscriptionPlanCommitmentInterval();
        $interval->setStartTime(time());
        $interval->setEndTime(time() + (86400 * 365));
        $plan->setCommitmentInterval($interval);
    */

    $subscription->setPlan($plan);

    // Subscriptions have an renewal setting.
    $renewal = new Google_RenewalSettings();
    $renewal->setRenewalType(ResellerRenewalType::AUTO_RENEW);
    $subscription->setRenewalSettings($renewal);

    // Each subscription needs a seat count.
    // Ideally this should pull the seat count from the previous domain.
    $seats = new Google_Seats();
    $seats->setMaximumNumberOfSeats($_POST['maximumNumberOfSeats']);
    $seats->setNumberOfSeats($_POST['numberOfSeats']);
    $subscription->setSeats($seats);

    $service->subscriptions->insert(
        $_POST['customerDomain'],
        $subscription,
        array(
            // The customerAuthToken is typically
            // referred to as the "Transfer Token"
            "customerAuthToken" => $_POST['customerAuthToken']
        )
    );

    // Draw a simple template.
    include 'templates/transfer.php';

?>