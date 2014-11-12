<?php
  require_once 'settings.php';
  require_once "app.php";
  require_once 'controllers.php';

  $app = new Application(array(
    '#\/$#'                                   => IndexHandler,
    '#\/api\/createCustomer$#'                => StepOneHandler,
    '#\/api\/createSubscription$#'            => StepTwoHandler,
    '#\/api\/getSiteValidationToken$#'        => StepThreeHandler,
    '#\/api\/testValidation$#'                => StepFourHandler,
    '#\/api\/createUser$#'                    => StepFiveHandler
  ));

  $app->run();
?>