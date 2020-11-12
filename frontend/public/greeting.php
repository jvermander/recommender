<?php
    error_reporting(-1);
    ini_set('display_errors', 'On');

    chdir('../../');
    $cmd = "env/bin/python3.5 backend/src/get_popular.py 2>&1";
    $json = shell_exec($cmd);
    echo $json;
?>