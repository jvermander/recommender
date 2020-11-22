#!/usr/bin/env python3.5
# Book recommender system:
# Matrix Factorization via Alternating Least Squares
import numpy as np
import pandas as pd

import scipy.sparse as sps
from scipy.sparse import csr_matrix

import implicit
from sklearn.model_selection import GridSearchCV, cross_val_score, KFold, StratifiedKFold, RandomizedSearchCV, train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity

import pickle
import difflib
# import Levenshtein as lev
import mysql.connector
import configparser

import csv
import time
import os
import glob
import sys

def main( argv ):
  try:
    user, train = int(argv[1]), int(argv[2])
  except:
    print('Usage: %s <user_id> <train>' % argv[0])
    exit()

  train_model() if train else load_model()
  json = recommend_for(user)
  print(json)

def load_data():
  config = configparser.ConfigParser()
  config.read('sql/database.ini')
  
  try:
    dbconn = mysql.connector.connect(
      host=config['database']['host'],
      user=config['database']['usr'],
      password=config['database']['pwd'],
      database=config['database']['name']
    )
    print('Successfully established a connection.')
  except Exception as e:
    print('Failed to establish a database connection.')
    print(e)
    sys.exit()

  try: 
    query = 'SELECT * FROM bookratings;'
    book_ratings = pd.read_sql(query, dbconn)

    query = 'SELECT * FROM authorratings;'
    auth_ratings = pd.read_sql(query, dbconn)

    query = 'SELECT * FROM books;'
    book_lookup = pd.read_sql(query, dbconn)

    query = 'SELECT * FROM authors;'
    auth_lookup = pd.read_sql(query, dbconn)

    query = 'SELECT * FROM users;'
    user_lookup = pd.read_sql(query, dbconn)

    dbconn.close()
    print('Successfully loaded data.')
  except Exception as e:
    print('Failed to fetch data.')
    print(e)
    sys.exit()
  
  return book_ratings, auth_ratings, book_lookup, auth_lookup, user_lookup

def train_model( path='models/impALS/', f1=200, f2=200, l1=1, l2=1 ):
  global book_model, auth_model, \
         all_book_ratings, all_auth_ratings, \
         book_lookup, auth_lookup, user_lookup
  
  all_book_ratings, all_auth_ratings, book_lookup, auth_lookup, user_lookup = load_data()

  book_model = implicit.als.AlternatingLeastSquares(iterations=5, factors=f1, regularization=l1, num_threads=0, calculate_training_loss=True)
  csr = get_books_csr()
  book_model.fit(csr.transpose())

  auth_model = implicit.als.AlternatingLeastSquares(iterations=5, factors=f2, regularization=l2, num_threads=0, calculate_training_loss=True)
  csr = get_auths_csr()
  auth_model.fit(csr.transpose())
  
  pickle.dump(book_model, open(path + 'impALSbooks.sav', 'wb'))
  pickle.dump(auth_model, open(path + 'impALSauthors.sav', 'wb'))
  pickle.dump(all_book_ratings, open(path + 'bookratings.sav', 'wb'))
  pickle.dump(all_auth_ratings, open(path + 'authratings.sav', 'wb'))
  pickle.dump(book_lookup, open(path + 'booklookup.sav', 'wb'))
  pickle.dump(auth_lookup, open(path + 'authlookup.sav', 'wb'))
  pickle.dump(user_lookup, open(path + 'userlookup.sav', 'wb'))

def load_model( path='models/impALS/' ):
  global book_model, auth_model, \
         all_book_ratings, all_auth_ratings, \
         book_lookup, auth_lookup, user_lookup

  book_model = pickle.load(open(path + 'impALSbooks.sav', 'rb'))
  auth_model = pickle.load(open(path + 'impALSauthors.sav', 'rb'))
  
  all_book_ratings = pickle.load(open(path + 'bookratings.sav', 'rb'))
  all_auth_ratings = pickle.load(open(path + 'authratings.sav', 'rb'))
  
  book_lookup = pickle.load(open(path + 'booklookup.sav', 'rb'))
  auth_lookup = pickle.load(open(path + 'authlookup.sav', 'rb'))
  user_lookup = pickle.load(open(path + 'userlookup.sav', 'rb'))

  return book_model, auth_model, \
         all_book_ratings, all_auth_ratings, \
         book_lookup, auth_lookup, user_lookup

#todo: remove debugging
def recommend_for( user, n=5 ):
  user_ratings = get_user_ratings(user)
  if(user_ratings.shape[0] < 1):
    return '[]'

  candidate_aids = pd.Series(name='AID')
  candidate_aids = candidate_aids.append(recommend_authors_by_item(user))
  candidate_aids = candidate_aids.append(recommend_authors_by_item_cosine(user))
  candidate_aids = candidate_aids.append(recommend_authors_by_user(user))
  author_ranking = rank_authors(user, candidate_aids)

  candidate_bids = pd.Series(name='BID')
  candidate_bids = candidate_bids.append(recommend_books_by_author(author_ranking))
  candidate_bids = candidate_bids.append(recommend_books_by_item(user))
  candidate_bids = candidate_bids.append(recommend_books_by_item_cosine(user))
  candidate_bids = candidate_bids.append(recommend_books_by_user(user))
  candidate_bids = remove_already_read(user_ratings, candidate_bids)
  book_ranking = rank_books(user, candidate_bids)
  
  book_recommendation = book_ranking[:n]

  bids = recommend_books_by_author(author_ranking)
  available_lookup = bids[(~bids.isin(book_recommendation.BID)) & (~bids.isin(user_ratings.BID))]
  available_lookup = lookup_books(available_lookup)
  counts = available_lookup.AID.value_counts()
  recommended_authors = author_ranking[author_ranking.AID.isin(counts.index)]
  recommended_authors = recommended_authors[:n]
  recommended_authors.reset_index(drop=True, inplace=True)
  
  author_recommendation = recommend_books_for_each_author(user, recommended_authors, available_lookup)

  json = to_json(user_ratings, book_recommendation, author_recommendation)
  return json

def to_json( ratings, books, authors ):
  columns = ['Title', 'Author', 'ISBN', 'Publisher', 'YearPublished', 'ImageURLL']

  ratings = ratings[columns + ['Score']].to_json(orient='records')
  books = books[columns].to_json(orient='records')

  json = "[" + ratings + ", " + books
  for i in range(len(authors)):
    json += ", "
    temp = authors[i][columns].to_json(orient='records')
    json += temp
  json += "]"

  return json

def get_user_ratings( user ):
  book_ratings = lookup_books(all_book_ratings[all_book_ratings.UID == user])
  return book_ratings

def lookup_books( bids ):
  bids = pd.DataFrame(bids)
  summary = bids.merge(book_lookup, on='BID', how='left')
  summary = summary.merge(auth_lookup, on='AID', how='left')
  return summary

def lookup_authors( aids ):
  aids = pd.DataFrame(aids)
  summary = aids.merge(auth_lookup, on='AID', how='left')
  return summary

def recommend_authors_by_item( user, thres=4.0, n=5 ):
  user_ratings = all_auth_ratings[all_auth_ratings.UID == user]
  aids = user_ratings[user_ratings.Score >= thres].AID
  aids.reset_index(drop=True, inplace=True)

  result = []
  csr = get_auths_csr()
  for i in range(aids.shape[0]):
    result += auth_model.similar_items(aids[i], N=n, react_users=csr.transpose())

  result = [x for x,_ in result]
  aids = pd.Series(result, name='AID')

  return aids

def recommend_authors_by_item_cosine( user, thres=4.0, n_similar=5 ):
  user_ratings = all_auth_ratings[all_auth_ratings.UID == user]
  top_ratings = user_ratings[user_ratings.Score >= thres]
  csr = get_auths_csr().transpose()
  similarities = pd.DataFrame(cosine_similarity(csr, csr[top_ratings.AID]))

  aids = np.argpartition(np.array(similarities), kth=-n_similar, axis=0)[-n_similar:]
  aids = pd.Series(aids.flatten(), name='AID')

  return aids

def recommend_authors_by_user( user, thres=4.0, n=5 ):
  uids = auth_model.similar_users(user, N=n)
  uids = [x for x,_ in uids]

  aids = all_auth_ratings[all_auth_ratings.UID.isin(uids)]
  aids = aids[aids.Score >= thres].AID
  aids.reset_index(drop=True, inplace=True)

  return aids

def rank_books( user, bids ):
  book_scores = score_by_book(user, bids)
  count = book_scores.groupby('BID').count()
  count.columns = ['Count']
  book_scores.drop_duplicates('BID', inplace=True)

  ranking = lookup_books(book_scores)
  ranking = ranking.merge(count, on='BID', how='left')
  
  ranking.sort_values(['Count', 'BookScore'], ascending=False, inplace=True)
  ranking.reset_index(drop=True, inplace=True)
  return ranking

def rank_authors( user, aids, thres=0.03 ):
  counts = pd.DataFrame(aids.value_counts())
  counts.reset_index(inplace=True)
  counts.columns = ['AID', 'Count']

  author_scores = score_by_author(user, counts.AID)
  authors = author_scores.merge(counts, on='AID', how='left')
  authors = lookup_authors(authors)
  authors['Overall'] = (authors['Count'] * authors['AuthScore']) 
  authors = authors[authors.Overall >= thres]
  authors.sort_values(['Count', 'AuthScore'], inplace=True, ascending=False)
  authors.reset_index(drop=True, inplace=True)
  
  return authors

def recommend_books_by_author( aids, pool=None ):
  if(pool is None):
    lookup = book_lookup
  else:
    lookup = pool
  aids = pd.DataFrame(aids)
  bids = aids.merge(lookup, on='AID', how='left').BID
  return bids

def recommend_books_by_item( user, thres=4.0, n=5 ):
  bids = all_book_ratings[all_book_ratings.UID == user]
  bids = bids[bids.Score >= thres].BID
  bids.reset_index(drop=True, inplace=True)

  result = []
  csr = get_books_csr()
  for i in range(bids.shape[0]):
    result += (book_model.similar_items(bids[i], N=n, react_users=csr.transpose()))
  result = [x for x,_ in result]
  bids = pd.Series(result)
  bids.name = 'BID'
  return bids

def recommend_books_by_item_cosine( user, thres=4.0, n_similar=5 ):
  user_ratings = all_book_ratings[all_book_ratings.UID == user]
  top_ratings = user_ratings[user_ratings.Score >= thres]
  csr = get_books_csr().transpose()
  similarities = pd.DataFrame(cosine_similarity(csr, csr[top_ratings.BID]))

  bids = np.argpartition(np.array(similarities), kth=-n_similar, axis=0)[-n_similar:]
  bids = pd.Series(bids.flatten(), name='BID')

  return bids

def recommend_books_by_user( user, thres=4.0, n=5 ):
  uids_tuples = book_model.similar_users(user, n)
  uids = [x for x, _ in uids_tuples]

  bids = all_book_ratings[all_book_ratings.UID.isin(uids)]
  bids = bids[bids.Score >= thres].BID
  bids.reset_index(drop=True, inplace=True)

  return bids

def remove_already_read( user_ratings, bids ):
  bids = bids[~bids.isin(user_ratings.BID)]
  return bids

def score_by_book( user, bids ):
  csr = get_books_csr()
  scores = book_model.rank_items(user, csr, bids.to_list())
  scores = pd.DataFrame(scores, columns=['BID', 'BookScore'])

  return scores

def score_by_author( user, aids ):
  csr = get_auths_csr()
  scores = auth_model.rank_items(user, csr, aids.to_list())
  scores = pd.DataFrame(scores, columns=['AID', 'AuthScore'])

  return scores

# Assemble a sparse matrix from a dataframe
def books_to_csr( ratings, shape ):
  data = ratings['Score']
  row_ind = ratings['UID']
  col_ind = ratings['BID']

  csr = csr_matrix((data, (row_ind, col_ind)), shape=shape)
  return csr

def get_auths_csr():
  return auths_to_csr(all_auth_ratings, (user_lookup.shape[0], auth_lookup.shape[0]))

def get_books_csr():
  return books_to_csr(all_book_ratings, (user_lookup.shape[0], book_lookup.shape[0]))

def auths_to_csr( ratings, shape ):
  data = ratings['Score']
  row_ind = ratings['UID']
  col_ind = ratings['AID']

  csr = csr_matrix((data, (row_ind, col_ind)), shape=shape)
  return csr

def remove_dup_rows( df ):
  df.drop_duplicates(inplace=True)

def detect_null( df ):
  print("\nNaN counts:\n")
  counts = df.isnull().sum(axis=0)
  out = pd.concat([counts, counts / df.shape[0]], axis=1)
  out.columns = ['NaN', 'Percent']
  print(out)
  print("\n")

def display_unique( df ):
  print("Unique counts:\n")
  counts = df.nunique()
  percent = counts.copy()
  percent.iloc[:] /= df.shape[0] 
  out = pd.concat([counts, percent], axis=1)
  out.columns = ['Unique', 'Percent']
  print(out)
  print("\n")

# Saves to file a subset of ratings made only by users with at least k distinct ratings
def lower_bound_ratings( ratings, k, path ):
  n = ratings.groupby(by=['UID']).count()
  n = n.where(cond=(n.BID >= k))
  n = n.dropna()
  n = set(n.index)

  ratings = ratings.loc[ratings['UID'].isin(n)].reset_index(drop=True)
  unique = pd.Series(pd.unique(ratings.UID)).to_dict()
  unique = {y:x for x,y in unique.items()}
  ratings.UID = ratings.UID.map(unique) # mapping for reindexing

  ratings.to_csv(path, sep=',', quoting=csv.QUOTE_NONNUMERIC, index=False)
  return ratings


def normalize_by_item_and_user( df, is_auths ):
  df, mu_i = normalize_by_item(df, is_auths)
  df, mu_u = normalize_by_user(df, is_auths)
  return df, mu_i, mu_u

# For each rating, subtracts the average rating for the associated item (column).
# Returns the vector of averages for later prediction
def normalize_by_item( df, is_auths ):
  if(is_auths):
    csr = authors_to_csr(df)
  else:
    csr = books_to_csr(df)

  sums = csr.sum(axis=0).flatten()
  counts = csr.getnnz(axis=0).flatten()
  mu = np.divide(sums, counts, out=np.zeros_like(sums), where=(counts != 0))
  mu = np.array(mu).flatten()

  if(is_auths):
    df.Score -= mu[df.AID]
  else:
    df.Score -= mu[df.BID]
  return df, mu

# For each rating, subtracts the average rating from the associated user (row).
# Returns the vector of averages for later prediction
def normalize_by_user( df, is_auths ):
  if(is_auths):
    csr = authors_to_csr(df)
  else:
    csr = books_to_csr(df)

  sums = csr.sum(axis=1).flatten()
  counts = csr.getnnz(axis=1).flatten()
  mu = np.divide(sums, counts, out=np.zeros_like(sums), where=(counts != 0))
  mu = np.array(mu).flatten()

  df.Score -= mu[df.UID]
  return df, mu

def recommend_books_for_each_author(user, recommended_authors, available, n=5):
  recommended_authors_books = []
  for i in range(recommended_authors.shape[0]):
    aid = pd.Series([recommended_authors.loc[i, 'AID']], name='AID')
    temp = book_model.rank_items(user, get_books_csr(), recommend_books_by_author(aid, available))
    temp = pd.DataFrame(temp, columns=['BID', 'BookScore'])[:n]
    temp = lookup_books(temp)
    recommended_authors_books.append(temp)
  return recommended_authors_books

if __name__ == "__main__":
  main(sys.argv)
