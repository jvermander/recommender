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
    $tok = mysqli_real_escape_string($link, $post['tok']);
    
    $sql = "SELECT UID FROM users WHERE usr='$usr'";
    $result = $link->query($sql);
    $uid = mysqli_fetch_assoc($result)['UID'];
    
    $sql = "SELECT Title, Author, ISBN, YearPublished, Publisher, ImageURLL, A.BID, A.AID, Score
            FROM ( SELECT BID, books.AID, ISBN, Title, Author, YearPublished, Publisher, ImageURLL
                   FROM books 
                   JOIN authors ON books.AID=authors.AID 
                   WHERE Title LIKE '%$tok%' OR Author LIKE '%$tok%' OR ISBN LIKE '$tok') AS A
            LEFT JOIN 
                 ( SELECT BID, Score 
                   FROM bookratings 
                   WHERE bookratings.UID=$uid) AS B
              ON A.BID=B.BID";
    try {
        $result = $link->query($sql);
        if(mysqli_connect_errno()) {
            http_response_code(500);
            throw new Exception(mysqli_connect_error());
        }
        // if($result->num_rows != 1) {
        //     http_response_code(401);
        //     throw new Exception('Authentication failed.');
        // }        
    } catch(Exception $e) {
        exit($e->getMessage());
    }
    
    $out = array();
    for($i = 0; $i < 25 && $i < $result->num_rows; $i++)
      array_push($out, mysqli_fetch_assoc($result));
    echo json_encode($out);
?>