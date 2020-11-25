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
    
    $sql = "SELECT UID FROM users WHERE usr='$usr'";
    $result = $link->query($sql);
    $uid = mysqli_fetch_assoc($result)['UID'];
    
    chdir('../../');
    $cmd = "env/bin/python3.5 backend/src/recommender.py $uid 1 2>&1";
    $json = shell_exec($cmd);
    echo $json;
?>