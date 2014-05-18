<?php

require_once "controllers.php";

class Application {
  /**
  This is a very simple attempt to emulate Python's webapp2.

  This code should be used as an example,
  and should not under any circumstances be used in production.
  **/

  protected $_ROUTES = array();

  function __construct($routes = array()) {
    $this->_ROUTES = $routes;
  }

  function run() {
    foreach($this->_ROUTES as $path => $controller) {
      if(preg_match($path, $_SERVER['PATH_INFO'])) {
        $controller = new $controller;
        $controller->_SERVER = $_SERVER;
        $controller->_SESSION = $_SESSION;
        $controller->_REQUEST = $_REQUEST;
        $request_method = strtolower($_SERVER['REQUEST_METHOD']);
        $result = call_user_func(array($controller, $request_method));
        if(is_array($result)) {
          header("Content-type: application/json");
          print json_encode($result);
        }
        exit();
      }
    }
  }
}

class RequestHandler {
  public $_SERVER = array();
  public $_SESSION = array();
  public $_REQUEST = array();

  private $_raw_body = "";
  protected $json_data = array();

  function __construct() {
    $this->_raw_body = @file_get_contents("php://input");
    $this->json_data = json_decode($this->_raw_body, true);
    //print_r($this->json_data);
  }

  function get() {}

  function post() {}

  function redirect($loc) {
    header("Location: ". $loc);
    exit();
  }

}
?>