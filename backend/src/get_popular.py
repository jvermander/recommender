import numpy as np
import pandas as pd
import recommender as rec

import sys
import random

def main( argv ):
  global book_model, auth_model, \
         all_book_ratings, all_auth_ratings, \
         book_lookup, auth_lookup, user_lookup

  (book_model, auth_model, \
  all_book_ratings, all_auth_ratings, \
  book_lookup, auth_lookup, user_lookup) = rec.load_model()
  
  # calc_avg_ratings()

  get_most_popular()

def get_most_popular( path='models/impALS/avg.csv', n=5, m=50 ):

  ratings = pd.read_csv(path)
  ratings['BID'] = ratings['BID'].astype(int)
  ratings.sort_values('Score', inplace=True, ascending=False)
  ratings = ratings.iloc[:m, :]
  ratings = ratings.iloc[random.sample(range(0, m), n)]
  ratings = ratings.merge(book_lookup, on='BID', how='left')
  ratings = ratings.merge(auth_lookup, on='AID', how='left')
  ratings.drop(columns=['Score', 'Total'], inplace=True)
  print("[" + ratings.to_json(orient='records') + "]")

def calc_avg_ratings( path='models/impALS/avg.csv' ):
  
  stars = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
  stars = pd.DataFrame(index=stars)
  stars['Count'] = 1
  book_ratings = all_book_ratings.groupby(['BID']).apply(calc_avg_rating, stars.copy())

  book_ratings['BID'] = book_ratings['BID'].astype(int)
  book_ratings.to_csv(path, index=False)

def calc_avg_rating( ratings, stars_counts ):
  
  N = ratings.shape[0]
  K = 10
  z = 1.65

  book_star_counts = pd.DataFrame(ratings.Score.value_counts())
  book_star_counts.columns = ['Count']
  total = book_star_counts.Count.sum(axis=0)
  star_counts = stars_counts.add(book_star_counts, fill_value=0)
  # print(ratings)
  # print(book_star_counts)
  A = np.sum(star_counts.index.values * star_counts.Count.values) / (N + K)
  B = np.sum(star_counts.index.values ** 2 * star_counts.Count.values) / (N + K)

  avg = A - z * np.sqrt((B - A ** 2) / (N + K + 1))
  ratings = ratings[['BID']]
  ratings = ratings.iloc[0]
  ratings['Score'] = avg
  ratings['Total'] = total
  ratings['BID'] = ratings['BID'].astype(int)

  return ratings



main(sys.argv)
