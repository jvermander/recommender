import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';

const books = [{Title: "null"}, {Title: "null"}, {Title: "null"}, {Title: "null"}, {Title: "null"}];

function Recommender() {
  const [isLogged, setIsLogged] = useState(false);
  const [username, setUsername] = useState(null);
  const [recommendations, setRecommendations] = useState(books);
  const [authors, setAuthors] = useState(null);

  const onLogin = (username, arr) => {
    if(arr.length > 0) {
      setRecommendations(arr[0]);
      if(arr.length > 1)
        setAuthors(arr.slice(1));
    } 
    setUsername(username);
    setIsLogged(true);

    console.log(recommendations)
    console.log(arr.slice(1))
    console.log(authors)
  }
  return(
    <div id='app' class='container-fluid text-center p-0'>
      <Navbar onLogin={onLogin}/>
      <Greeting isLogged={isLogged} authors={authors} username={username} recommendations={recommendations}/>
      <Authors authors={authors}/>
    </div>
  );
}

function Navbar(props) {
  const [isLogged, setIsLogged] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async(event) => {
    event.preventDefault();
    let usr = event.target.parentElement.parentElement.usr.value;
    let pwd = event.target.parentElement.parentElement.pwd.value;

    const postobj = {usr: usr, pwd: pwd};
    try {
      setIsLoading(true);
      let reply = await axios.post('login.php', postobj);
      let arr = reply.data;
      console.log('In handleLogin');
      console.log(reply.data)

      // authentication success
      setIsLogged(true);

      // check if user has personalized recommendations
      if(arr.length == 0)
        console.log('No Ratings!');
      props.onLogin(usr, arr)
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
      <form class='ml-auto' method="POST" container='container-fluid border'>
      <fieldset disabled={isLoading}>
        <input type="text" name="usr" placeholder="Username" autocomplete="off"></input>
        <input type="password" name="pwd" placeholder="Password" autocomplete="off"></input>
        <button type="submit" onClick={handleLogin}>Login</button>  
        <button type="submit" onClick={handleRegister}>Register</button>
      </fieldset>
      </form>;
  } else {
      html = <form class='ml-auto'><fieldset><div>Logged In...</div></fieldset></form>
  }
  return (<div id='navbar' class='navbar sticky-top container-fluid p-3 mt-2 justify-content-right'> {html} </div>);
}

function Greeting(props) {
  const isLogged = props.isLogged;
  // const hasRated = props.hasRated;
  const username = props.username;
  const recommendations = props.recommendations;

  const unloggedHeader = 'Need a book to read?';
  const defaultSubtitle = 'Rate books, get recommendations! Here are some popular titles ...';
  const ratedSubtitle = 'What similar users are currently reading'

  const [header, setHeader] = useState(unloggedHeader);
  const [subtitle, setSubtitle] = useState(defaultSubtitle);

  // On login/logout
  useEffect(() => {

    if(isLogged) {
      setHeader('Welcome, ' + username + '!');
      console.log(props.authors)
      setSubtitle(ratedSubtitle);
    } else {
      setHeader(unloggedHeader);
      setSubtitle(defaultSubtitle);
    }

  }, [isLogged])

  return (
    <div>
      <div class='container-fluid p-4 text-center border'>
        <span class='fancy header'>{header}</span>
        <div class='text-center pt-1'><img  height='auto' width='2.5%' src='assets/separator.png'/></div>
        <span class='fancy subtitle'>{subtitle}</span>
      </div>

      <div class='container'>
            <BookList books={props.recommendations} />
      </div>
    </div>
  );
}

function BookList(props) {
  const books = props.books;
  const listItems = books.map((book, index) => {
    let temp = 'https://images-na.ssl-images-amazon.com/images/I/41DxTj1cWoL._SX316_BO1,204,203,200_.jpg';

    let margin = '0.5em';
    if(index % 2 == 0) {
      temp = 'https://images-na.ssl-images-amazon.com/images/I/51Pli1sEdvL._SX348_BO1,204,203,200_.jpg';
      margin = '-0.5em';
    }
    
    temp = book.ImageURLL == null ? temp : book.ImageURLL;
    return (
    <div class='col-2 ' style={{zIndex: index+1}}>
      <Book src={temp} margin={margin}/>
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

function Book(props) {
  const summarize = (event) => {
    event.preventDefault();
    window.alert('Clicked');
    console.log('Clicked');
  }

  return (
    <img class='book' onClick={summarize} style={{marginTop: props.margin}}  height='100%' width='150%' src={props.src}/>
  );
}

function Authors(props) {
  const authors = props.authors;
  const defaultHeader = 'Authors you may like';

  let listItems = null;
  if(authors != null) {
    listItems = authors.map((author, index) => {
      return ( 
        <div class='row my-5 py-5'>
          <div class='border p-0 m-0 col-3 justify-content-center' style={{verticalAlign: 'middle'}}>{author[0].AuthorName}</div>
          <div class='border p-0 m-0 col-1 justify-content-center'>~</div>
          <div class='col-8 p-0 m-0 border '> 
            <BookList books={author}/>
          </div>
        </div>

      );
    })
  }

  let html = null;
  if(authors != null) {
    html = 
    <div class='container-fluid mt-5 pt-5 border'>
      <span class='fancy header'>{defaultHeader}</span>
      <div class='text-center pt-1 pb-0'><img  height='auto' width='2.5%' src='assets/separator.png'/></div>
      {listItems}
    </div>
  }

  return html;
}

ReactDOM.render(<Recommender/>, document.getElementById('root'));