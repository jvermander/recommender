import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';

const books = [{Title: "null1"}, {Title: "null2"}, {Title: "null3"}, {Title: "null4"}, {Title: "null5"}];

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
  return (
    <div id='navbar' class='navbar sticky-top container-fluid p-3 mt-2 justify-content-right'>
      <img height='auto' width='3%' src='assets/logo2.png'></img>
      {html} 
    </div>);
}

function Greeting(props) {
  const isLogged = props.isLogged;
  // const hasRated = props.hasRated;
  const username = props.username;
  const recommendations = props.recommendations;

  const unloggedHeader = 'Need a book to read?';
  const defaultSubtitle = 'Rate books, get recommendations! Here are some popular titles.';
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
    <div class='container-fluid'>
      <div class='row p-4 m-0 justify-content-center align-items-center'>
        <div class='fancy header'>{header}</div>
        <div class='divider text-center m-2'>|</div>
        <div class='fancy subtitle'>{subtitle}</div>
      </div>

      <div class='container'>
            <BookList books={props.recommendations} />
      </div>
    </div>
  );
}

function BookList({books, faceLeft=true}) {
  const [title, setTitle] = useState('-\n-');
  const listItems = books.map((book, index, arr) => {
    let temp = 'https://images-na.ssl-images-amazon.com/images/I/41DxTj1cWoL._SX316_BO1,204,203,200_.jpg';

    let margin = '0.5em';
    if(index % 2 == 0) {
      temp = 'https://images-na.ssl-images-amazon.com/images/I/51Pli1sEdvL._SX348_BO1,204,203,200_.jpg';
      margin = '-0.5em';
    }

    const onHover = (title) => {
      setTitle(title);
    }

    var newZIndex = faceLeft ? index+1 : arr.length - index;

    temp = book.ImageURLL == null ? temp : book.ImageURLL;
    return (
    <div class='col-2 ' style={{zIndex: newZIndex}}>
      <Book src={temp} title={book.Title} margin={margin} faceLeft={faceLeft} onHover={onHover}/>
    </div>
    );
  });
  
  let highlighted

  return(
    <div class='container border'>
      <div class='row'>
        <div class='col-1'></div>
        {listItems}
        <div class='col-1'></div>
      </div>
      <div class='row py-5 px-0 my-4 justify-content-center fancy border' width='100%' style={{fontSize: '2em', display: 'block'}}>{title}</div>
    </div>
  );
}

function Book({margin, src, title, faceLeft, onHover}) {
  const summarize = (event) => {
    event.preventDefault();
    window.alert('Clicked');
    console.log('Clicked');
  }

  const entered = (event) => {
    onHover(title);
  }

  const left = (event) => {
    onHover('-\n-');
  }

  let className = 'book '.concat(faceLeft ? 'left' : 'right');
  return (
    <img class={className} onMouseEnter={entered} onMouseLeave={left} onClick={summarize} style={{marginTop: margin}} height='100%' width='150%' src={src}/>
  );
}

function Authors(props) {
  const authors = props.authors;
  const defaultHeader = 'Your Author List';
  const defaultSubtitle = 'Authors we think you\'ll like';

  let listItems = null;
  if(authors != null) {
    listItems = authors.map((author, index, arr) => {
      let html;
      let authorname = <div class='col-4 px-5 authorname text-center align-self-center' style={{bottom: '1.5em'}}>{author[0].AuthorName}</div>;
      let books = <div class='col-8'><BookList books={author} faceLeft={index%2 == 0}/></div>;
      
      if(index % 2 == 0) {
        html = 
          <div class='row my-5 py-5  '>
            {authorname}
            {books}
          </div>;
      } else {
        html = 
          <div class='row my-5 py-5 '>
            {books}
            {authorname}
          </div>;
      }
      return html;
    })
  }

  let html = null;
  if(authors != null) {
    html = 
    <div class='container-fluid mt-5 pt-5'>
      <div class='row p-4 m-0 justify-content-center align-items-center'>
        <div class='fancy header'>{defaultHeader}</div>
        <div class='divider text-center m-2'>|</div>
        <div class='fancy subtitle'>{defaultSubtitle}</div>
      </div>
      {listItems}
    </div>
  }
  return html;
}

ReactDOM.render(<Recommender/>, document.getElementById('root'));