import React, { useState, useEffect, useLayoutEffect } from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';

function Recommender({popular, onload}) {
  const [isLogged, setIsLogged] = useState(false);
  const [username, setUsername] = useState(null);
  const [recommendations, setRecommendations] = useState(popular);
  const [ratings, setRatings] = useState(null);
  const [sessionRatings, setSessionRatings] = useState(0);
  const [isTraining, setIsTraining] = useState(null);

  const [focusedId, setFocusedId] = useState('landing');
  const [focusedBook, setFocusedBook] = useState(null);

  const TRAIN_THRESHOLD = 1;

  const onLogin = (username, arr) => {
    contentTransition(() => {
      if(arr.length > 0)
        setRatings(arr[0])
      if(arr.length > 1)
        setRecommendations(arr.slice(1));
      setUsername(username);
      setIsLogged(true);
      
      console.log(arr);

      if(arr.length > 0) {
        console.log("Ratings: ");
        console.log(arr[0])
        setFocusedId('recommendation');
      } else {
        setFocusedId('search');
      }
      if(arr.length > 1) {
        console.log("Recommendations:");
        console.log(arr[1]);
      }
      if(arr.length > 2) {
        console.log("Authors:");
        console.log(arr.slice(2));
      }
    })
  }

  const onLogout = () => {
    contentTransition(() => {
      setUsername(null);
      setIsLogged(false);
      setRecommendations(popular);
      setRatings(null);
      setSessionRatings(0);
      setFocusedId('landing');
    });
  }

  const onRate = async(book) => {
    // update the client
    let temp = [...ratings];
    temp.push(book);
    setRatings(temp);

    // update the server
    let postobj = {usr: username, rating: JSON.stringify(book)};
    let reply = await axios.post('rate.php', postobj).then((reply)=>{
      setSessionRatings(sessionRatings+1);
    });

  }

  const onSummary = (book) => {
    setFocusedBook(book);
  }

  const toRecommendation = () => {
    if(focusedId != 'recommendation') {
      contentTransition(() => {
        setFocusedId('recommendation');
      });
    }
  }

  const toRatings = () => {
    if(focusedId != 'ratings') {
      contentTransition(() => {
        setFocusedId('ratings');
      });
    }
  }

  const toSearch = () => {
    if(focusedId != 'search') {
      contentTransition(() => {
        setFocusedId('search');
      })
    }
  }

  const contentTransition = (func) => {
    document.getElementById(focusedId).classList.add('fadeoutfast');
    setTimeout(() => {
      func();
      document.getElementById(focusedId).classList.remove('fadeoutfast');
    }, 500)
  }

  useEffect(() => {
    console.log(focusedId);
    document.getElementById(focusedId).classList.add('fadeinfast');
    setTimeout(() => {
      document.getElementById(focusedId).classList.remove('fadeinfast');
    }, 500)
  }, [focusedId])

  useEffect(async() => {
    if(sessionRatings == TRAIN_THRESHOLD) {
      console.log('Re-training model...');
      setIsTraining(true);
      let reply = await axios.post('retrain.php', {usr: username}).then((reply) => {
        let arr = reply.data;
        console.log(arr);
        if(arr.length > 0)
          setRatings(arr[0])
        if(arr.length > 1)
          setRecommendations(arr.slice(1));
        setSessionRatings(0);
        setIsTraining(false);
      });
    }
  }, [sessionRatings]);

  useEffect(() => {
    onload();
  }, []);

  return(
    <div class='container-fluid text-center p-0 m-0'>
      <Navbar isTraining={isTraining} onLogin={onLogin} onLogout={onLogout} toRatings={toRatings} toRecommendation={toRecommendation} toSearch={toSearch}/>
      <Landing popular={popular} onSummary={onSummary} focusedId={focusedId}/>
      <Recommendation recommendations={recommendations} username={username} hasRated={ratings != null} onSummary={onSummary} focusedId={focusedId}/>
      <Ratings ratings={ratings} onSummary={onSummary} focusedId={focusedId}/>
      <Search username={username} onSummary={onSummary} focusedId={focusedId}/>
      <Footer/>
      <BookModal book={focusedBook} isLogged={isLogged} onSummary={onSummary} onRate={onRate}/>
    </div>
  );
}

function Landing({popular, onSummary, focusedId}) {
  const id = 'landing';
  const listId = 'landinglist'
  const header = 'Need a book to read?';
  const subtitle = 'Rate books, get recommendations! Here are some popular titles.';

  return(
    <div id={id} class='container-fluid' style={{display: focusedId == id? 'block' : 'none'}}>
      <Header header={header} subtitle={subtitle}/>
      <Carousel content={popular} id={listId} onSummary={onSummary}/>
    </div>
  );
}

function Recommendation({recommendations, username, hasRated, onSummary, focusedId}) {
  const id = 'recommendation';
  const listId = 'recommendationlist'
  
  const authorsHeader = 'Your Author List';
  const authorsSubtitle = 'Authors we think you\'ll like';
  const ratedSubtitle = 'What similar users are reading';
  const unratedSubtitle = 'Try rating some books to get special recommendations!';

  const [header, setHeader] = useState(null);
  const [subtitle, setSubtitle] = useState(null);

  const onIndexChange = (oldIndex, newIndex) => {
    if(oldIndex == 0) {
      document.getElementById('recheader').classList.add('fadeoutfast');
      setTimeout(() => {
        document.getElementById('recheader').classList.remove('fadeoutfast');
        setHeader(authorsHeader);
        setSubtitle(authorsSubtitle);
      }, 500);
    } else if(newIndex == 0) {
      document.getElementById('recheader').classList.add('fadeoutfast');
      setTimeout(() => {
        document.getElementById('recheader').classList.remove('fadeoutfast');
        setHeader('Welcome ' + username + '!');
        setSubtitle(hasRated? ratedSubtitle : unratedSubtitle);
      }, 500);
    };
  }

  useEffect(() => {
    document.getElementById('recheader').classList.add('fadeinfast');
    setTimeout(() => {
      document.getElementById('recheader').classList.remove('fadeinfast');
    }, 500);
  }, [header]);

  useEffect(() => {
    setHeader('Welcome ' + username + '!');
    setSubtitle(hasRated? ratedSubtitle : unratedSubtitle);
  }, [username, hasRated]);


  return(
    <div id={id} class='container-fluid' style={{display: focusedId == id? 'block' : 'none'}}>
      <div id='recheader'>
        <Header header={header} subtitle={subtitle}/>
      </div>
      {username != null? <Carousel content={recommendations} id={listId} onSummary={onSummary} showAuthor={true} onIndexChange={onIndexChange}/> : null}
    </div>
  );
}

const makeSlice = (ratings, n=5) => {
  let i = 0;
  let j = 0;
  let result = [];
  while(i < ratings.length) {
    j = i + n;
    result.push(ratings.slice(i, j));
    i = j;
  }
  return result;
};

function Ratings({ratings, onSummary, focusedId}) {
  const id = 'ratings';
  const listId = 'ratingslist';

  const header = 'Your ratings';
  const ratedSubtitle = 'What you\'ve already read';
  const unratedSubtitle = 'You have none!';

  const [content, setContent] = useState(null);

  useEffect(() => {
    if(ratings != null) 
      setContent(makeSlice(ratings));
    else
      setContent(null);
  }, [ratings]);

  return (
    <div id={id} class='container-fluid' style={{display: focusedId == id? 'block' : 'none'}}>
      <Header header={header} subtitle={ratedSubtitle}/>
      {content != null? <Carousel content={content} id={listId} onSummary={onSummary}/> : 
       <div class='pt-5 mt-5' style={{fontFamily: 'fairy', fontSize: '100px', color: 'white', opacity: 0.5}}>
         You have no ratings!
       </div>}
    </div>
  );
  
}

function Search({username, onSummary, focusedId}) {
  const id = 'search';
  const listId = 'searchlist';
  const [content, setContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const [header, setHeader] = useState('Book Search');
  const [subtitle, setSubtitle] = useState('Find books to rate');

  const makeQuery = async() => {
    let querytext = document.getElementById('querytext');
    if(querytext.value != '') {
      let postobj = {tok: querytext.value, usr: username}
      setIsLoading(true);
      let reply = await axios.post('search.php', postobj);
      console.log(reply.data);
      if(reply.data.length > 0)
        setContent(makeSlice(reply.data));
      setIsLoading(false);
    }
  }

  const onExit = () => {
    setContent(null);
  }

  useEffect(() => {
    if(content == null) {
      document.getElementById('querytext').value = '';
    }

    if(username == null) {
      setContent(null);
    }
  }, [username, content])

  let html;
  if(content != null) {
    html =
      <div id={id} class='container-fluid align-items-center' style={{display: focusedId == id? 'block' : 'none'}}>
        <Header header={header} subtitle={subtitle}></Header>
        <div>
          <div class='exitBtn m-0 p-0' onClick={onExit} style={{position: 'absolute', fontFamily: 'fairy', fontSize: '36px', top: '22.5%', left: '82.5%', zIndex: 10}}>X</div>
          <Carousel content={content} id={listId} onSummary={onSummary}/>
        </div>
      </div>
  } else {
    html = 
      <div id={id} class='container-fluid justify-content-center' style={{display: focusedId == id? 'block' : 'none'}}>
        <Header header={header} subtitle={subtitle}></Header>
        <div class='row' style={{pointerEvents: isLoading? 'none' : 'all'}}>
          <div class='col-3'></div>
          <div class='col-6 pt-5 mt-5 justify-self-center'>
            <div class='row justify-content-center'>
              <input id='querytext' class='col booksearchbar' type='text' placeholder='Search by title, author or ISBN'></input>
            </div>
            <div class='row '>
              <div class='col-1 searchBtn floating m-0 p-0' onClick={makeQuery}>&gt;</div>  
            </div>
          </div>
          <div class='col-3'></div>
        </div>
      </div>
  }

  return html;
}

function Header({header, subtitle}) {
  return(
    <div class='row p-4 m-0 justify-content-center align-items-center'>
      <div class='fancy header'>{header}</div>
      <div class='divider text-center m-2'>|</div>
      <div class='fancy subtitle'>{subtitle}</div>
    </div>
  );
}

function BookModal({book, isLogged, onSummary, onRate}) {
  const [rating, setRating] = useState(0);
  const [existing, setExisting] = useState(false);

  const exit = (event) => {
    if(rating != 0 && !existing) {
      book.Score = rating;
      onRate(book);
    }
    onSummary(null);
  }

  const starOnClick = (event) => {
    event.preventDefault();
    let id = event.target.id;
    setRating(id != rating? id : 0);
  }

  useEffect(() => {
    if(book != null && 'Score' in book && book.Score != null) {
      console.log(Math.round(book.Score));
      setRating(Math.round(book.Score));
      setExisting(true);
    } else {
      setRating(0);
      setExisting(false);
    }
  }, [book]);

  useEffect(() => {
    if(rating != 0) {
      let element = document.getElementById(rating);
      let current = element;
      while(current != null) {
        current.classList.add('staractive');
        current = current.previousSibling;
      }
      current = element.nextSibling;
      while(current != null) {
        current.classList.remove('staractive');
        current = current.nextSibling;
      }
    } else {
      let element = document.getElementById(1);
      let current = element;
      while(current != null) {
        current.classList.remove('staractive');
        current = current.nextSibling;
      }
    }
    
    if(book != null) {
      let desc = document.getElementById('ratingdesc');
      if(rating == 0) {
        desc.innerHTML = 'You haven\'t rated this book yet';
      } else if(rating == 1) {
        desc.innerHTML = 'Your rating - Terrible';
      } else if(rating == 2) {
        desc.innerHTML = 'Your rating - Poor';
      } else if(rating == 3) {
        desc.innerHTML = 'Your rating - Average';
      } else if(rating == 4) {
        desc.innerHTML = 'Your rating - Good';
      } else if(rating == 5) {
        desc.innerHTML = 'Your rating - Amazing';
      }
    }
  }, [rating]);

  let modal = null;
  if(book != null) {
    let stringContent = 
    <div class="modalText" style={{fontSize: '26px', fontFamily: 'fairy', lineHeight: '2em'}}>
    <div><span>Title</span> • <span>{book.Title}</span></div>
    <div><span>Author</span> • <span>{book.Author}</span></div>
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
      <div class='p-0 m-0 exitBtn' style={{position: "absolute", top: 0, right: 0, fontSize: '36px'}} onClick={exit}>X</div>
      <div class='p-0 m-0 floating searchBtn' style={{position: "absolute", bottom: 0, right: 0, fontSize: '40px'}}>Purchase Now &gt;&gt;</div>
      <div>
        <div class='row'>
          <img src={book.ImageURLL} class='p-2' style={{border: '1px solid white'}}></img>
        </div>
        <div style={{display: isLogged? 'block' : 'none'}}>
          <div id='ratingdesc' class='row justify-content-center fancy' style={{fontSize: '24px'}}>You haven't rated this book yet</div>
          <div class='row justify-content-center'>
            <div class='star' id='1' onClick={existing? null : starOnClick}></div>
            <div class='star' id='2' onClick={existing? null : starOnClick}></div>
            <div class='star' id='3' onClick={existing? null : starOnClick}></div>
            <div class='star' id='4' onClick={existing? null : starOnClick}></div>
            <div class='star' id='5' onClick={existing? null : starOnClick}></div>
          </div>
        </div>
      </div>
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

function Navbar({onLogin, onLogout, toRatings, toRecommendation, toSearch, isTraining}) {
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

  var trainText;
  if(isTraining == null) {
    trainText = '';
  } else if(isTraining) {
    trainText = 'We are finding recommendations for you...';
  } else if(!isTraining) {
    trainText = 'You have new recommendations!';
  }

  useEffect(() => {
    document.getElementById('trainText').style.opacity = isTraining? 1 : 0;
  }, [isTraining]);

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
          <button class='btn btn-dark mr-1' onClick={toRecommendation}>My Recommendations</button>
          <button class='btn btn-dark mr-1' onClick={toSearch}>Search Books</button>
          <button class='btn btn-dark mr-1' onClick={toRatings}>My Ratings</button>
          <button class='btn btn-dark' onClick={handleLogout}>Logout</button>
        </div>
  }
  return (
    <div class='navbar bar sticky-top p-2 mt-2 text-left'>
      <div class='col m-0 p-0'><a href="#"><img class='mx-2' height='auto' width='50px' src='assets/logo2.png'></img></a></div>
      <div id='trainText' class='m-0 p-0' style={{animation: isTraining? 'flash 1.5s infinite':"none"}}>{trainText}</div>
      {html} 
    </div>);
}


// Expects an array of arrays
function Carousel({content, id, showAuthor=false, onIndexChange=null, onSummary}) {
  const [index, setIndex] = useState(0);
  const [rightClicked, setRightClicked] = useState(null);

  const clickRight = () => {
    let booklist = document.getElementById(id);
    booklist.classList.add('fadeoutleft');

    let newIndex = (index+1) % content.length;
    if(onIndexChange != null) 
      onIndexChange(index, newIndex);
    setTimeout(() => {
      setIndex(newIndex);
    }, 500);
  }

  const clickLeft = () => {
    let booklist = document.getElementById(id);
    booklist.classList.add('fadeoutright');

    let l = content.length;
    let newIndex = (((index-1) % l) + l) % l;
    if(onIndexChange != null)
      onIndexChange(index, newIndex);
    setTimeout(() => {
      setIndex(newIndex);
    }, 500);
  }

  useEffect(() => {
    let booklist = document.getElementById(id);
    if(booklist.classList.contains('fadeoutleft')) {
      booklist.classList.remove('fadeoutleft');
      booklist.classList.add('fadeinright');
      setTimeout(() => {
        booklist.classList.remove('fadeinright');
      }, 500);
    } else if(booklist.classList.contains('fadeoutright')) {
      booklist.classList.remove('fadeoutright');
      booklist.classList.add('fadeinleft');
      setTimeout(() => {
        booklist.classList.remove('fadeinleft');
      }, 500);
    }
  }, [index]);

  useEffect(() => {
    setIndex(0);
  }, [content]);

  return (
    <div class='row m-0 justify-content-center'>
      <div class='col align-items-top m-0 p-0 justify-content-right'>
        <div style={{position: 'relative', top: '12.5vh'}} class='row justify-content-center'>
          <div class='carouselBtn p-0' onClick={clickLeft} style={{display: content.length > 1? 'flex' : 'none'}}>&lt;</div>
        </div>
      </div>
      <BookList id={id} books={content[index]} onSummary={onSummary} showAuthor={showAuthor && index != 0}/>
      <div class='col align-items-top m-0 p-0'>
        <div style={{position: 'relative', top: '12.5vh'}} class='row justify-content-center'>
          <div class='carouselBtn p-0' onClick={clickRight} style={{display: content.length > 1? 'flex' : 'none'}}>&gt;</div>
        </div>
      </div>
    </div>
  );
}

function BookList({books, id, faceLeft=true, onSummary, showAuthor}) {
  const [title, setTitle] = useState(showAuthor ? books[0].Author : '-');
  const [opacity, setOpacity] = useState(showAuthor ? 1: 0);
  const [font, setFont] = useState('fairy');
  const [fontSize, setFontSize] = useState('2em');

  const listItems = books.map((book, index, arr) => {
    let margin = index % 2 == 0 ? '-0.5em' : '0.5em';

    const onHover = (string) => {
      setOpacity(string == null ? 0 : 1);
      if(string == null) {
        if(showAuthor) {
          setTitle(books[0].Author);
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
      setTitle(books[0].Author);
      setOpacity(1);
      setFont('fairyb');
      setFontSize('3em');
    } else {
      setOpacity(0);
    }
  }, [showAuthor, books])

  return(
    <div id={id} class='container m-0 justify-self-center'>
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






