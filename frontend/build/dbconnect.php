<?php
error_reporting(-1);
ini_set('display_errors', 'On');
function dbconnect() {
    // set_error_handler(function(){});
    static $link;
    if(!isset($link)) {
        $creds = parse_ini_file("../../sql/database.ini");
        $link = mysqli_connect($creds['host'], $creds['usr'], $creds['pwd'], $creds['name']);
    }
    return $link;
}
?>