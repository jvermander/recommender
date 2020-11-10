import React, { useState, useEffect, useLayoutEffect } from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';

const books = [{Title: "null1"}, {Title: "null2"}, {Title: "null3"}, {Title: "null4"}, 
               {Title: "null-------------------------------------------------------------------------- \
               --------------------------------------------------------------"}];

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
    <div class='container-fluid text-center p-0 mb-0'>
      <Navbar onLogin={onLogin}/>
      <Greeting isLogged={isLogged} authors={authors} username={username} recommendations={recommendations}/>
      <Authors authors={authors}/>
      <Footer/>
    </div>
  );
}

function Navbar(props) {
  const [isLogged, setIsLogged] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const validate_credentials = () => {
    let usrfield = document.getElementById('usrfield');
    let usrfeedback = document.getElementById('usrfeedback');
    let pwdfield = document.getElementById('pwdfield');
    let pwdfeedback = document.getElementById('pwdfeedback');

    let isUsrValid = usrfield.checkValidity();
    let isPwdValid = pwdfield.checkValidity();

    if(!isUsrValid) {
      let errmsg = "";
      if(usrfield.validity.valueMissing)
        errmsg = "Required";
      else if(usrfield.validity.patternMismatch)
        errmsg = "Must be alphanumeric between 3 and 15 characters";
      usrfeedback.innerHTML = errmsg;
    }
    if(!isPwdValid) {
      let errmsg = "";
      if(pwdfield.validity.valueMissing)
        errmsg = "Required";
      else if(pwdfield.validity.patternMismatch)
        errmsg = "Must be at least 4 characters";
      pwdfeedback.innerHTML = errmsg;
    }

    usrfeedback.style.visibility = isUsrValid ? 'hidden' : 'visible';
    pwdfeedback.style.visibility = isPwdValid ? 'hidden' : 'visible';

    return (isUsrValid) && (isPwdValid);
  }

  const handleLogin = async(event) => {
    event.preventDefault();
    let form = event.target.parentElement.parentElement;

    if(validate_credentials()) {
      let usr = form.usr.value.trim();
      let pwd = form.pwd.value;
      const postobj = {usr: usr, pwd: pwd};
      try {
        setIsLoading(true);
        let reply = await axios.post('login.php', postobj);
        let arr = reply.data;
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
        let usrfeedback = document.getElementById('usrfeedback');
        usrfeedback.style.visibility = 'visible';
        usrfeedback.innerHTML = 'Incorrect username or password';
      } finally {
        setIsLoading(false);
      }
    }
  }

  const handleRegister = async(event) => {
    event.preventDefault();
    let form = event.target.parentElement.parentElement;

    if(validate_credentials()) {
      let usr = form.usr.value.trim();
      let pwd = form.pwd.value;
      const postobj = {usr: usr, pwd: pwd};
      try {
        setIsLoading(true);
        let reply = await axios.post('register.php', postobj);
        let arr = reply.data;
        console.log(reply.data)

        let usrfeedback = document.getElementById('usrfeedback');
        usrfeedback.style.visibility = 'visible';
        usrfeedback.innerHTML = 'Success - Please login';
      } catch(e) {
        // registration failure
        console.log(e);
        let usrfeedback = document.getElementById('usrfeedback');
        usrfeedback.style.visibility = 'visible';
        usrfeedback.innerHTML = 'Username already exists';

      } finally {
        setIsLoading(false);
      }
    }
  }

  var html;
  if(!isLogged) {
      html =
      <form method='POST' class='ml-auto my-0'>
      <fieldset class='form-row' disabled={isLoading}>
        <div class='col m-0 p-0 form-group'>
          <input id='usrfield' type="text" name="usr" placeholder="Username" autocomplete="off" 
                 pattern='[a-zA-Z0-9_]{3,15}' required></input>
          <div id='usrfeedback' class='tooltiptext'></div>
        </div>
        <div class='col m-0 p-0 form-group'>
          <input id='pwdfield' type="password" name="pwd" placeholder="Password" autocomplete="off" 
                 pattern='.{4,256}' required></input>
          <div id='pwdfeedback' class='tooltiptext'></div>
        </div>
        
        <button class='btn btn-dark' type="submit" onClick={handleLogin}>Login</button>  
        <button class='btn btn-dark' type="submit" onClick={handleRegister}>Register</button>
      </fieldset>
      </form>;
  } else {
      html = 
        <div>
          <button class='btn btn-dark mr-1'>Your Ratings</button>
          <a href="#authors">
            <button class='btn btn-dark mr-1'>Your Authors</button>
          </a>
          <button class='btn btn-dark'>Logout</button>
        </div>
  }
  return (
    <div class='navbar bar sticky-top p-2 mt-2 text-left'>
      <div class='col m-0 p-0'><a href="#root"><img class='mx-2' height='auto' width='50px' src='assets/logo2.png'></img></a></div>
      {html} 
    </div>);
}

function Greeting({isLogged, username, recommendations, authors}) {

  const unloggedHeader = 'Need a book to read?';
  const defaultSubtitle = 'Rate books, get recommendations! Here are some popular titles.';
  const ratedSubtitle = 'What similar users are currently reading'

  const [header, setHeader] = useState(unloggedHeader);
  const [subtitle, setSubtitle] = useState(defaultSubtitle);

  // On login/logout
  useEffect(() => {
    if(isLogged) {
      setHeader('Welcome, ' + username + '!');
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
            <BookList books={recommendations} />
      </div>
    </div>
  );
}

function BookList({books, faceLeft=true}) {
  const [title, setTitle] = useState('-');
  const [opacity, setOpacity] = useState(0);
  const listItems = books.map((book, index, arr) => {
    let temp = 'https://images-na.ssl-images-amazon.com/images/I/41DxTj1cWoL._SX316_BO1,204,203,200_.jpg';

    let margin = '0.5em';
    if(index % 2 == 0) {
      temp = 'https://images-na.ssl-images-amazon.com/images/I/51Pli1sEdvL._SX348_BO1,204,203,200_.jpg';
      margin = '-0.5em';
    }

    const onHover = (string) => {
      setOpacity(string == null ? 0 : 1);
      setTitle(string == null ? title : string);
    }

    var newZIndex = faceLeft ? index+1 : arr.length - index;

    temp = book.ImageURLL == null ? temp : book.ImageURLL;
    return (
    <div class='col-2' style={{zIndex: newZIndex}}>
      <Book src={temp} title={book.Title} margin={margin} faceLeft={faceLeft} onHover={onHover}/>
    </div>
    );
  });  

  return(
    <div class='container'>
      <div class='row'>
        <div class='col-1'></div>
        {listItems}
        <div class='col-1'></div>
      </div>
      <div class='row py-5 px-0 my-4 fancy bookname' style={{opacity: opacity}}>{title}</div>
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
    onHover(null);
  }

  let className = 'book '.concat(faceLeft ? 'left' : 'right');
  return (
    <img class={className} onMouseEnter={entered} onMouseLeave={left} onClick={summarize} style={{marginTop: margin}} height='100%' width='150%' src={src}/>
  );
}

// Random fancy author name fonts
const FONTS = ['fairyb', 'mephisto', 'k22', 'alice', 'wonderland', 'nightmare', 'blkchcry', 'achaf'];
function getRandomFont() {
  let min = 0;
  let max = FONTS.length-1;

  min = Math.ceil(min);
  max = Math.floor(max);
  let i = Math.floor(Math.random() * (max - min + 1)) + min;

  return FONTS[i];
}

function Authors(props) {
  const authors = props.authors;
  const defaultHeader = 'Your Author List';
  const defaultSubtitle = 'Authors we think you\'ll like';

  let listItems = null;
  if(authors != null) {
    listItems = authors.map((author, index, arr) => {
      let html;
      let authorname = <div class='col-4 px-5 authorname text-center align-self-center' style={{fontFamily: getRandomFont(), left: index%2==0?'1em':'-0.5em'}}>{author[0].AuthorName}</div>;
      let books = <div class='col-8'><BookList books={author} faceLeft={index%2 == 0}/></div>;
      
      if(index % 2 == 0) {
        html = 
          <div class='row my-0 py-4'>
            {authorname}
            {books}
          </div>;
      } else {
        html = 
          <div class='row my-0 py-4'>
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
    <div id='authors' class='container-fluid my-5 pt-5'>
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

function Footer() {
  return (
      <div class='footer row fancy bar align-items-center mx-0 mb-0 p-2'>
        <div class='col p-0 m-0'>Author: Joe Vermander</div>
        <div class='divider text-center p-0 m-0' style={{fontSize: '2em'}}>-</div>
        <div class='col p-0 m-0'>E-mail: jlvermander@gmail.com</div>
        <div class='divider text-center p-0 m-0' style={{fontSize: '2em'}}>-</div>
        <div class='col'>GitHub: https://github.com/jvermander</div>
      </div>
  );
}

ReactDOM.render(<Recommender/>, document.getElementById('root'));