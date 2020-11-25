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
    $rating = json_decode($post['rating']);
    
    $sql = "SELECT UID FROM users WHERE usr='$usr'";
    $result = $link->query($sql);
    $uid = mysqli_fetch_assoc($result)['UID'];

    $bid = $rating->{'BID'};
    $score = $rating->{'Score'};

    $sql = "INSERT INTO bookratings VALUES ($uid, $bid, $score)";
    $link->query($sql);

    $aid = $rating->{'AID'};
    $sql = "SELECT AVG(Score) AS avg FROM bookratings LEFT JOIN books ON bookratings.BID=books.BID WHERE AID=$aid AND bookratings.UID=$uid";
    $result = $link->query($sql);
    $result = mysqli_fetch_assoc($result);
    $avg = $result['avg'];
    $sql = "INSERT INTO authorratings VALUES ($uid, $aid, $avg) ON DUPLICATE KEY UPDATE UID=$uid, AID=$aid, Score=$avg";
    $result = $link->query($sql);
?>