import React, { useState, useEffect, useLayoutEffect } from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';

function Recommender({popular, onload}) {
  const [isLogged, setIsLogged] = useState(false);
  const [username, setUsername] = useState(null);
  const [recommendations, setRecommendations] = useState(popular);

  const [focusedBook, setFocusedBook] = useState(null);

  const onLogin = (username, arr) => {
    if(arr.length > 0)
      setRecommendations(arr);
    setUsername(username);
    setIsLogged(true);

    if(arr.length > 0) {
      console.log("Recommendations:");
      console.log(arr[0]);
      if(arr.length > 1) {
        console.log("Authors:");
        console.log(arr.slice(1));
      }
    }
  }

  const onLogout = () => {
    setUsername(null);
    setRecommendations(popular);
    setIsLogged(false);
  }

  const onSummary = (book) => {
    setFocusedBook(book);
  }

  useEffect(() => {
    onload();
  }, []);

  return(
    <div class='container-fluid text-center p-0 m-0'>
      <Navbar onLogin={onLogin} onLogout={onLogout}/>
      <Carousel isLogged={isLogged} username={username} recommendations={recommendations} popular={popular} onSummary={onSummary}/>
      <Footer/>
      <BookModal book={focusedBook} onSummary={onSummary}/>
    </div>
  );
}

function BookModal({book, onSummary}) {
  const exit = (event) => {
      onSummary(null);
  }

  let modal = null;
  if(book != null) {
    let stringContent = 
    <div class="modalText" style={{fontSize: '26px', fontFamily: 'fairy', lineHeight: '2em', }}>
    <div><span>Title</span> • <span>{book.Title}</span></div>
    <div><span>Author</span> • <span>{book.AuthorName}</span></div>
    <div><span>Year Published</span> • <span>{book.YearPublished}</span></div>
    <div><span>Publisher</span> • <span>{book.Publisher}</span></div>
    <div><span>ISBN</span> • <span>{book.ISBN}</span></div>
  </div>

    modal = 
    <div class='p-4' 
      style={{  
                zIndex: 51, display: 'flex',
                justifyContent: 'center',
                flexDirection: 'row', justifyContent: 'right', alignItems: 'center',
                position: 'fixed'}}>
      <div class='p-0 m-0' id='modalexit' style={{position: "absolute", top: 0, right: 0, fontSize: '36px'}} onClick={exit}>X</div>
      <div><img src={book.ImageURLL} class='p-2' style={{border: '1px solid white'}}></img></div>
        {stringContent}
    </div>;
  }

  return(
    <div id='bookModalBackground' 
      style={{
        zIndex:50, 
        display: book == null ? 'none' : 'flex',
        overflow: 'hidden',
        position: 'fixed', top: 0, left: 0, height: '100vh', width: '100%',
        justifyContent: 'center', alignItems: 'center',
        backgroundColor: 'rgba(0,0,0,0.90)',
        fontFamily: 'fairy'
      }}>
      {modal}
    </div>
  );
}

function Navbar({onLogin, onLogout}) {
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
        errmsg = "Required.";
      else if(usrfield.validity.patternMismatch)
        errmsg = "Must be alphanumeric, between 3 and 15 characters.";
      usrfeedback.innerHTML = errmsg;
    }
    if(!isPwdValid) {
      let errmsg = "";
      if(pwdfield.validity.valueMissing)
        errmsg = "Required.";
      else if(pwdfield.validity.patternMismatch)
        errmsg = "Must be at least 4 characters.";
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
        console.log("Server data:");
        console.log(reply.data);

        // authentication success
        setIsLogged(true);
        onLogin(usr, arr)
      } catch(e) {
        // authentication failure
        console.log(e);
        let usrfeedback = document.getElementById('usrfeedback');
        usrfeedback.style.visibility = 'visible';
        usrfeedback.innerHTML = 'Incorrect username or password.';
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

        reply = await axios.post('login.php', postobj);
        arr = reply.data;
        console.log("Server data:");
        console.log(reply.data)

        // registration, and thus authentication success
        setIsLogged(true);
        onLogin(usr, arr)
      } catch(e) {
        // registration failure
        console.log(e);
        let usrfeedback = document.getElementById('usrfeedback');
        usrfeedback.style.visibility = 'visible';
        usrfeedback.innerHTML = 'Username already exists.';

      } finally {
        setIsLoading(false);
      }
    }
  }

  const handleLogout = () => {
    setIsLogged(false);
    onLogout();
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
          <button class='btn btn-dark mr-1'>Rate Books</button>
          <button class='btn btn-dark mr-1'>Your Books</button>
          <button class='btn btn-dark' onClick={handleLogout}>Logout</button>
        </div>
  }
  return (
    <div class='navbar bar sticky-top p-2 mt-2 text-left'>
      <div class='col m-0 p-0'><a href="#root"><img class='mx-2' height='auto' width='50px' src='assets/logo2.png'></img></a></div>
      {html} 
    </div>);
}

function Carousel({isLogged, username, recommendations, popular, onSummary}) {
  const genericHeader = 'Need a book to read?';
  const genericSubtitle = 'Rate books, get recommendations! Here are some popular titles.';

  const userSubtitle = 'What similar users are currently reading';

  const authorsHeader = 'Your Author List';
  const authorsSubtitle = 'Authors we think you\'ll like';

  const [header, setHeader] = useState(genericHeader);
  const [subtitle, setSubtitle] = useState(genericSubtitle);
  const [index, setIndex] = useState(0);
  
  const [rightClicked, setRightClicked] = useState(null);

  // On login/logout
  useEffect(() => {
    if(isLogged) {
        setHeader(index == 0 ? 'Welcome ' + username + '!' : authorsHeader);
        setSubtitle(index == 0 ? userSubtitle : authorsSubtitle);
    } else {
        setIndex(0);
        setHeader(genericHeader);
        setSubtitle(genericSubtitle);
    }
    setTimeout(() => {
      document.getElementById('headercontainer').style.animation = 'fadeIn 500ms';
      document.getElementById('headercontainer').style.visibility = 'visible';
    }, 200);
  }, [isLogged, index])

  const clickRight = () => {
    let newIndex = (index+1) % recommendations.length;
    if(index == 0 || newIndex == 0) {
      document.getElementById('headercontainer').style.animation = 'fadeOut 500ms';
      document.getElementById('headercontainer').style.visibility = 'hidden';
    }

    let booklist = document.getElementById('booklist');
    booklist.style.animationName = 'fadeOutLeft';
    booklist.style.animationDuration = '500ms';
    booklist.style.animationTimingFunction = 'ease-in';
    booklist.style.visibility = 'hidden';
    setTimeout(() => {
      setIndex(newIndex);
      setRightClicked(true);
    }, 500);
  }

  const clickLeft = () => {
    let l = recommendations.length;
    let newIndex = (((index-1) % l) + l) % l;
    if(index == 0 || newIndex == 0) {
      document.getElementById('headercontainer').style.animation = 'fadeOut 500ms';
      document.getElementById('headercontainer').style.visibility = 'hidden';
    }

    let booklist = document.getElementById('booklist');
    booklist.style.animationName = 'fadeOutRight';
    booklist.style.animationDuration = '500ms';
    booklist.style.animationTimingFunction = 'ease-in';
    booklist.style.visibility = 'hidden';
    setTimeout(() => {
      setIndex(newIndex);
      setRightClicked(false);
    }, 500);

  }

  useEffect(() => {
    let booklist = document.getElementById('booklist');
    if(booklist.style.visibility == 'hidden') {
      setTimeout(() => {
        if(rightClicked)
          booklist.style.animation = 'fadeInRight 500ms ease-out';
        else
          booklist.style.animation = 'fadeInLeft 500ms ease-out';
        booklist.style.visibility = 'visible';
      }, 200);
    }
  });

  let className = 'col'.concat(isLogged && recommendations !== popular ? ' fadein' : null);
  return (
    <div class={className}>
      <div id='headercontainer' class='row p-4 m-0 justify-content-center align-items-center'>
        <div class='fancy header'>{header}</div>
        <div class='divider text-center m-2'>|</div>
        <div class='fancy subtitle'>{subtitle}</div>
      </div>
      <div class='row m-0 justify-content-center'>
        <div class='col align-items-top m-0 p-0 justify-content-right'>
          <div style={{position: 'relative', top: '12.5vh'}} class='row justify-content-center'>
            <div class='carouselBtn p-0' onClick={clickLeft} style={{display: isLogged ? 'flex' : 'none'}}>&lt;</div>
          </div>
        </div>
        <BookList books={recommendations[isLogged? index : 0]} onSummary={onSummary} showAuthor={isLogged? index != 0: false}/>
        <div class='col align-items-top m-0 p-0'>
          <div style={{position: 'relative', top: '12.5vh'}} class='row justify-content-center'>
            <div class='carouselBtn p-0' onClick={clickRight} style={{display: isLogged ? 'flex' : 'none'}}>&gt;</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function BookList({books, faceLeft=true, onSummary, showAuthor}) {
  const [title, setTitle] = useState(showAuthor ? books[0].AuthorName : '-');
  const [opacity, setOpacity] = useState(showAuthor ? 1: 0);
  const [font, setFont] = useState('fairy');
  const [fontSize, setFontSize] = useState('2em');

  const listItems = books.map((book, index, arr) => {
    let margin = index % 2 == 0 ? '-0.5em' : '0.5em';

    const onHover = (string) => {
      setOpacity(string == null ? 0 : 1);
      if(string == null) {
        if(showAuthor) {
          setTitle(books[0].AuthorName);
          setOpacity(1);
          setFont('fairyb');
          setFontSize('3em');
        } else {
          setTitle(title);
          setOpacity(0);
          setFont('fairy');
          setFontSize('2em');
        }
      } else {
        setTitle(string);
        setOpacity(1);
        setFont('fairy');
        setFontSize('2em');
      }
    }

    var newZIndex = faceLeft ? index+1 : arr.length - index;
    return (
    <div class='col-2' style={{zIndex: newZIndex, height: '42.5vh'}}>
      <Book book={book} margin={margin} faceLeft={faceLeft} onHover={onHover} onSummary={onSummary}/>
    </div>
    );
  });  

  useEffect(() => {
    if(showAuthor) {
      setTitle(books[0].AuthorName);
      setOpacity(1);
      setFont('fairyb');
      setFontSize('3em');
    } else {
      setOpacity(0);
    }
  }, [showAuthor, books])

  return(
    <div  id='booklist'  class='container m-0 justify-self-center'>
      <div class='row justify-content-center'>
        <div class='col-1'></div>
        {listItems}
        <div class='col-1'></div>
      </div>
      <div class='row py-5 px-0 my-4 fancy bookname' style={{opacity: opacity, fontFamily: font, fontSize: fontSize}}>{title}</div>
    </div>
  );
}

function Book({margin, book, faceLeft, onHover, onSummary}) {

  const clicked = (event) => {
    event.preventDefault();
    onSummary(book);
  }

  const entered = (event) => {
    onHover(book.Title);
  }

  const left = (event) => {
    onHover(null);
  }

  let className = 'book'.concat(faceLeft ? ' left' : ' right');
  return (
      <img class={className} 
           onMouseEnter={entered} 
           onMouseLeave={left} 
           onClick={clicked} 
           src={book.ImageURLL} 
           style={{marginTop: margin, marginLeft: '-2vw'}} height='100%' width='150%'/>
  );
}

// Random fancy author name fonts
const FONTS = ['fairyb', 'mephisto', 'k22', 'alice', 'wonderland', 'nightmare', 'blkchcry', 'achaf'];
var randomFonts = getRandomFonts();

function getRandomFonts(n=5) {
  let fonts = [];
  for(var i = 0; i < n; i++) {
    let min = 0;
    let max = FONTS.length-1;

    min = Math.ceil(min);
    max = Math.floor(max);
    let i = Math.floor(Math.random() * (max - min + 1)) + min;
    fonts.push(FONTS[i]);
  }
  return fonts;
}

// function Authors({authors, onSummary}) {
//   const defaultHeader = 'Your Author List';
//   const defaultSubtitle = 'Authors we think you\'ll like';

//   let listItems = null;
//   if(authors != null) {
//     listItems = authors.map((author, index, arr) => {
//       let html;
//       let authorname = <div class='authorname text-center align-self-center pb-5' style={{fontFamily: 'fairyb'}}>{author[0].AuthorName}</div>;
//       let books = <div class='col'><BookList books={author} onSummary={onSummary}/></div>;
      

//         html = 
//           <div class='my-0 py-4'>
//             {authorname}
//             {books}
//           </div>;

//       return html;
//     })
//   }

//   let html = null;
//   if(authors != null) {
//     html =
//     <div id='authors' class='container justify-content-center'>
//       <div class='row p-4 m-0 mb-5 justify-content-center align-items-center'>
//         <div class='fancy header'>{defaultHeader}</div>
//         <div class='divider text-center m-2'>|</div>
//         <div class='fancy subtitle'>{defaultSubtitle}</div>
//       </div>
//       {listItems}
//     </div>
//   }
//   return html;
// }

function Footer() {
  let className = 'page-footer row fancy bar align-items-center mx-0 mb-0 p-2'.concat(true ? ' fixed-bottom' : null);
  return (
      <div class={className}>
        <div class='col p-0 m-0'>Author: Joe Vermander</div>
        <div class='divider text-center p-0 m-0' style={{fontSize: '2em'}}>-</div>
        <div class='col p-0 m-0'>E-mail: jlvermander@gmail.com</div>
        <div class='divider text-center p-0 m-0' style={{fontSize: '2em'}}>-</div>
        <div class='col'>GitHub: https://github.com/jvermander</div>
      </div>
  );
}

function LoadingScreen({isLoading}) {
  return (
    <div style={{display: isLoading ? 'flex' : 'none'}} class='loadingScreen sticky-top'>
      <div class='loadingScreenText'>Loading ...</div>
    </div>
  )
}

function App() {
  const [popular, setPopular] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const onload = () => {
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  }

  useEffect(() => {
    axios.get('greeting.php').then((reply) => { 
      console.log(reply.data);
      setPopular(reply.data);
    });
  }, [])

  let html;
  if(popular != null) {
    html = 
      <div>
        <LoadingScreen isLoading={isLoading}/>
        <Recommender popular={popular} onload={onload}/>
      </div>
  } else {
    html = <LoadingScreen isLoading={true}/>
  }

  return html;
}

ReactDOM.render(<App/>, document.getElementById('root')); 






