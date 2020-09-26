<?php
    error_reporting(-1);
    ini_set('display_errors', 'On');

    require_once 'dbconnect.php';
    $link = dbconnect();
    if($link === false) {
        exit("Failed to establish a database connection.");
    }
    $sql = "SELECT * FROM accounts WHERE usr='{$_POST['usr']}' AND pwd='{$_POST['pwd']}'";
    $result = $link->query($sql);
    if($result === false) {
        echo "Database query failed.";
    } else if($result->num_rows == 1) {    
        echo "Authentication successful.";
    } else {
        $failed = true;
        include 'index.php';
    }
?>