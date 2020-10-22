import React from 'react';
import ReactDOM from 'react-dom';

function BookList(props) {
  const books = props.books;
  const listItems = books.map((book) => <li>{book}</li>);

  return(
    <ul>{listItems}</ul>
  );
}

const books = ['The Republic', 'Candide', 'Beyond Good & Evil', 'Crime & Punishment', 'Gulag Archipelago']
ReactDOM.render(<BookList books={books}></BookList>, document.getElementById('booklist'))