<?php
    error_reporting(-1);
    ini_set('display_errors', 'On');

    require_once 'dbconnect.php';
    $link = dbconnect();
    if(mysqli_connect_errno()) {
      exit('Failed to connect to database: ' . mysqli_connect_error());
  }

    $usr = $_POST['usr'];
    $pwd = $_POST['pwd'];

    $sql = "SELECT * FROM users WHERE usr='$usr'";

    try {
      $result = $link->query($sql);
      if($result->num_rows != 0) {
        throw new Exception('Username already exists.');
      }
      
      $sql = "SHOW TABLE STATUS LIKE 'users'";
      $result = mysqli_fetch_array($link->query($sql));
      $UID = $result['Rows'];
      
      $sql = "INSERT INTO users VALUES($UID, '$usr', SHA('$pwd'))";
      $link->query($sql);

      echo "Registration successful for $UID";


    } catch(Exception $e) {
      exit($e->getMessage());
    }
?>