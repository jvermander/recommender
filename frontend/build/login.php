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

    $sql = "SELECT * FROM users WHERE usr='$usr' AND pwd=SHA('$pwd')";
    try {
        $result = $link->query($sql);
        if(mysqli_connect_errno()) {
            throw new Exception(mysqli_connect_error());
        }
        if($result->num_rows != 1) {
          throw new Exception('Authentication failed.');
        }
        echo('Authentication successful.');
    } catch(Exception $e) {
        exit($e->getMessage());
    }
?>