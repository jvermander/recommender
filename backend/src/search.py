import numpy as np
import pandas as pd
import recommender as rec

import sys
import random

from difflib import SequenceMatcher

def similar(a, b):
  return SequenceMatcher(None, a, b).ratio()


def main( argv ):
  global book_model, auth_model, \
         all_book_ratings, all_auth_ratings, \
         book_lookup, auth_lookup, user_lookup

  (book_model, auth_model, \
  all_book_ratings, all_auth_ratings, \
  book_lookup, auth_lookup, user_lookup) = rec.load_model()
  

  # token = argv[1]
  token = 'orwell'
  lookup = book_lookup.merge(auth_lookup, on='AID', how='left')
  print(lookup)


  lookup = lookup.apply(lambda x: search(x, token), axis=1)
  print(lookup)


def search(x, token):
  a = similar(x.Title, token)
  b = similar(x.Author, token)
  c = similar(x.ISBN, token)
  c = c if c == 1 else 0

  likeness = a if a > b else b
  likeness = likeness if likeness > c else c

  return [x.Title, likeness]

main(sys.argv)
