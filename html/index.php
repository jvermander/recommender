<!DOCTYPE html>
<html>
<head>
    <title>Authentication</title>
</head>
<body style="background-color: black;">
    <hr/>
    <form method="POST" action="auth.php">
        <input type="text" name="usr" placeholder="Username" autocomplete="off"></input> </br>
        <input type="password" name="pwd" placeholder="Password" autocomplete="off"></input> </br>
        <button type="submit">Login</button>  
        <button type="submit" formaction="register.php">Register</button>
    </form>
    <hr/>
    <div style="color: white;">
    </div> <br/>

</body>
</html>
