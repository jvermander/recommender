import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';

const books = [{Title: 'AAAAAAAAAAAAAAAAAAA AAAAAAAAAAAA'}, 
               {Title: 'Candide'}, 
               {Title:'Beyond Good & Evil'}, 
               {Title:'Crime & Punishment'}, 
               {Title:'Gulag Archipelago'}];

function Recommender() {
  const [recommendations, setRecommendations] = useState(books);

  const onLogin = (recommendations) => {
    console.log(recommendations);
    console.log(recommendations[0]);
    setRecommendations(recommendations[0]);

  }

  return(
    <div id='app' class='container-fluid p-0'>
      <div id='navbar' class='container-fluid border p-3 '>
        <Credentials onLogin={onLogin}/>
      </div>


      <div class='col-*-12'>Most Popular Titles</div>
      <div id='' class='container border'>
        <BookList books={recommendations} />
        {/* <BookList books={recommendations} />
        <BookList books={recommendations} />
        <BookList books={recommendations} />
        <BookList books={recommendations} />
        <BookList books={recommendations} /> */}
      </div>
    </div>
  );
}

function Credentials(props) {
  const [username, setUsername] = useState(null);
  const [isLogged, setIsLogged] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async(event) => {
    event.preventDefault();
    console.log(event.target);
    let usr = event.target.parentElement.parentElement.usr.value;
    let pwd = event.target.parentElement.parentElement.pwd.value;

    const postobj = {usr: usr, pwd: pwd};
    try {
      setIsLoading(true);
      let reply = await axios.post('login.php', postobj);
      let arr = reply.data;

      // authentication success
      setIsLogged(true);
      setUsername(usr);

      // check if user has personalized recommendations
      if(arr.length == 0)
        throw 'No Ratings!';
      props.onLogin(arr)
    } catch(e) {
      // authentication failure
      console.log(e);
    } finally {
      setIsLoading(false);
    }
  }

  const handleRegister = event => {
    event.preventDefault();
    console.log(event.target.parentElement.usr.value);

  }
  
  var html;
  if(!isLogged) {
      html =
      <form method="POST" container='container-fluid border'>
      <fieldset disabled={isLoading}>
        <input type="text" name="usr" placeholder="Username" autocomplete="off"></input>
        <input type="password" name="pwd" placeholder="Password" autocomplete="off"></input>
        <button type="submit" onClick={handleLogin}>Login</button>  
        <button type="submit" onClick={handleRegister}>Register</button>
      </fieldset>
      </form>;
  } else {
      html = <fieldset><div>Logged In as {username}</div></fieldset>
  }
  return html;
}

function BookList(props) {
  const books = props.books;
  const listItems = books.map((book, index) => {
    let temp = 'https://images-na.ssl-images-amazon.com/images/I/41DxTj1cWoL._SX316_BO1,204,203,200_.jpg';

    let margin = '5px';
    if(index % 2 == 0) {
      temp = 'https://images-na.ssl-images-amazon.com/images/I/51Pli1sEdvL._SX348_BO1,204,203,200_.jpg';
      margin = '-5px';
    }
    
    temp = book.ImageURLL == null ? temp : book.ImageURLL;
    console.log(temp)

    return (
    <div class='col-2 border'>
      <img class='' style={{zIndex: index+1, marginTop: margin, border: '5px solid black', boxShadow: '0 4px 8px 0 rgba(0, 0, 0, 0.5), 0 6px 20px 0 rgba(0, 0, 0, 0.4)'}} height='100%' width='150%' src={temp}/>
    </div>
    );
  });

  return(
    <div class='row m-0'>
      <div class='col-1'></div>
      {listItems}
      <div class='col-1'></div>
    </div>
  );
}

ReactDOM.render(<Recommender/>, document.getElementById('root'));