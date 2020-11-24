<?php
    error_reporting(-1);
    ini_set('display_errors', 'On');

    require_once 'dbconnect.php';
    $link = dbconnect();
    if(mysqli_connect_errno()) {
      exit('Failed to connect to database: ' . mysqli_connect_error());
  }

    $post = json_decode(file_get_contents('php://input'), true);
    $usr = $post['usr'];
    $pwd = $post['pwd'];

    $sql = "SELECT * FROM users WHERE usr='$usr'";

    try {
      $result = $link->query($sql);
      if($result->num_rows != 0) {
        http_response_code(401);
        throw new Exception('Username already exists.');
      }
      
      $sql = "SELECT COUNT(*) FROM users";
      $result = mysqli_fetch_array($link->query($sql));
      $UID = $result['COUNT(*)'];
      
      $sql = "INSERT INTO users VALUES($UID, '$usr', SHA('$pwd'))";
      $link->query($sql);

      echo "Registration successful for UID $UID.";

    } catch(Exception $e) {
      exit($e->getMessage());
    }
?>