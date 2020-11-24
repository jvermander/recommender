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
    
    $sql = "SELECT * FROM users WHERE usr='$usr' AND pwd=SHA('$pwd')";
    try {
        $result = $link->query($sql);
        if(mysqli_connect_errno()) {
            http_response_code(500);
            throw new Exception(mysqli_connect_error());
        }
        if($result->num_rows != 1) {
            http_response_code(401);
            throw new Exception('Authentication failed.');
        }        
    } catch(Exception $e) {
        exit($e->getMessage());
    }
    
    # Authentication successful
    $uid = mysqli_fetch_assoc($result)['UID'];
    chdir('../../');
    $cmd = "env/bin/python3.5 backend/src/recommender.py $uid 0 2>&1";
    $json = shell_exec($cmd);
    echo $json;
?>