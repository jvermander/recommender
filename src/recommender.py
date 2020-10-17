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
import Levenshtein as lev

import csv
import time
import os
import glob

TRAIN_DIR = 'data/train10'
BOOKS_CSV = 'data/booksdataset.csv'
AUTHS_CSV = 'data/authsdataset.csv'

#6590 - 10

user = 6589
def main():
  # files = glob.glob(TRAIN_DIR + '/*.csv')
  # df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
  # df.sort_values('UID', inplace=True)
  # df.reset_index(drop=True, inplace=True)

  # df.to_csv(TRAIN_DIR + '/books10.csv', index=False, quoting=csv.QUOTE_NONNUMERIC)


  # lookup = pd.read_csv(BOOKS_CSV, sep=';')
  # ratings = pd.read_csv(TRAIN_DIR + '/books10.csv')
  # ratings = ratings.merge(lookup, on='BID', how='left')

  # ratings = pd.DataFrame(ratings.groupby(['UID', 'AID']).Score.mean())
  # ratings.reset_index(inplace=True)
  # ratings.to_csv(TRAIN_DIR + '/authors10.csv', index=False, quoting=csv.QUOTE_NONNUMERIC)

  books = pd.read_csv(TRAIN_DIR + '/books10.csv')
  auths = pd.read_csv(TRAIN_DIR + '/authors10.csv')

  path = 'models/impALS'
  # train_model(books, auths, path)
  book_model, auth_model = load_model(path)
  recommend(books, auths, book_model, auth_model)



def train_model( books, authors, path, f1=200, f2=200, l1=1, l2=1 ):
  model = implicit.als.AlternatingLeastSquares(iterations=5, factors=f1, regularization=l1, num_threads=4, calculate_training_loss=True)
  csr = books_to_csr(books)
  model.fit(csr.transpose())
  pickle.dump(model, open(path + '/impALSbooks.sav', 'wb'))

  model = implicit.als.AlternatingLeastSquares(iterations=5, factors=f2, regularization=l2, num_threads=4, calculate_training_loss=True)
  csr = authors_to_csr(authors)
  model.fit(csr.transpose())
  pickle.dump(model, open(path + '/impALSauthors.sav', 'wb'))

def load_model( path ):
  book_model = pickle.load(open(path + '/impALSbooks.sav', 'rb'))
  auth_model = pickle.load(open(path + '/impALSauthors.sav', 'rb'))
  
  return book_model, auth_model

# todo: establish database, clean-up
 # Authors
  # -) Authors already liked
  # 1) Users that like author X also like ... (item-item)
  # 2) Users like you also like author Y ... (user-user)
  # 3) Predicted 

  # Books
  # -) Books by authors already liked
  # 1) Users that like book X also like ... (item-item)
  # 2) Users like you also like book Y ... (user-user)
  # 3) Predicted

  # 1) What similar users are reading
  # 2) Authors you may like
  # 3) Top authors

  # Books

  # 1) What other users are reading
  # 2) Authors you may like

def recommend( books, auths, book_model, auth_model ):
  global user

  print("User %d's ratings: " % user)
  user_ratings = get_user_ratings(user, books)
  print(user_ratings)

  candidate_authors = pd.Series(name='AID')
  candidate_authors = candidate_authors.append(recommend_authors_by_item(user, auth_model, auths))
  candidate_authors = candidate_authors.append(get_similar_authors(user, auths))
  candidate_authors = candidate_authors.append(recommend_authors_by_user(user, auth_model, auths))

  author_ranking = rank_authors(user, auth_model, auths, candidate_authors)

  candidates = pd.Series(name='BID')
  candidates = candidates.append(recommend_books_by_author(author_ranking))
  candidates = candidates.append(recommend_books_by_item(user, book_model, books))
  candidates = candidates.append(get_similar_books(user_ratings, books))
  candidates = candidates.append(recommend_books_by_user(user, book_model, books))

  candidates = remove_already_read(user_ratings, candidates)

  book_scores = score_by_book(user, book_model, books, candidates)
  aids = lookup_books(candidates).AID
  auth_scores = score_by_author(user, auth_model, auths, aids)

  book_ranking = rank_books(book_scores, auth_scores)
  
  recommended_books = book_ranking[:5]
  recommended_authors = author_ranking[:5]
  recommended_authors_books = recommend_books_for_each_author(recommended_authors, book_model, books)

  print(recommended_books)
  print(recommended_authors)
  print(recommended_authors_books)


def recommend_books_for_each_author(recommended_authors, model, ratings, n=5):
  recommended_authors_books = []
  for i in range(recommended_authors.shape[0]):
    aid = pd.Series([recommended_authors.loc[i, 'AID']], name='AID')
    temp = model.rank_items(user, books_to_csr(ratings), recommend_books_by_author(aid))
    temp = pd.DataFrame(temp, columns=['BID', 'BookScore'])[:5]
    temp = lookup_books(temp)
    recommended_authors_books.append(temp)
  return recommended_authors_books

def recommend_authors_by_item( user, model, ratings, thres=4.0, n=5 ):
  user_ratings = ratings[(ratings.UID == user)]
  user_authors = user_ratings[user_ratings.Score >= thres].AID
  user_authors.reset_index(drop=True, inplace=True)

  result = []
  csr = authors_to_csr(ratings)
  for i in range(user_authors.shape[0]):
    result += (model.similar_items(user_authors[i], N=n, react_users=csr.transpose()))

  recommended_authors = [x for x,_ in result]
  recommended_authors = pd.Series(recommended_authors, name='AID')

  return recommended_authors

def recommend_authors_by_user( user, model, ratings, thres=4.0, n=5 ):
  uids = model.similar_users(user, N=n)
  uids = [x for x,_ in uids]

  recommended_authors = ratings[ratings.UID.isin(uids)]
  recommended_authors = recommended_authors[recommended_authors.Score >= thres].AID
  recommended_authors.reset_index(drop=True, inplace=True)

  return recommended_authors

def rank_authors( user, model, ratings, ids, thres=0.02 ):
  counts = pd.DataFrame(ids.value_counts())
  counts.reset_index(inplace=True)
  counts.columns = ['AID', 'Count']
  author_scores = score_by_author(user, model, ratings, counts.AID)
  authors = author_scores.merge(counts, on='AID', how='left')
  authors = lookup_authors(authors)
  authors = authors[authors.AuthScore >= thres]
  authors.sort_values(['Count','AuthScore'], inplace=True, ascending=False)
  authors.reset_index(drop=True, inplace=True)

  return authors

def get_similar_books( user_ratings, ratings, thres=4.0, n_similar=5 ):
  top_ratings = user_ratings[user_ratings.Score >= thres]
  csr = books_to_csr(ratings).transpose()
  similarities = pd.DataFrame(cosine_similarity(csr, csr[top_ratings.BID]))

  ids = np.argpartition(np.array(similarities), kth=-n_similar, axis=0)[-n_similar:]
  ids = pd.Series(ids.flatten(), name='BID')

  return ids

def get_similar_authors( user, ratings, thres=4.0, n_similar=5 ):
  user_ratings = ratings[ratings.UID == user]
  top_ratings = user_ratings[user_ratings.Score >= thres]
  csr = authors_to_csr(ratings).transpose()
  similarities = pd.DataFrame(cosine_similarity(csr, csr[top_ratings.AID]))

  ids = np.argpartition(np.array(similarities), kth=-n_similar, axis=0)[-n_similar:]
  ids = pd.Series(ids.flatten(), name='AID')

  return ids

def lookup_books( bids ):
  lookup = pd.read_csv(BOOKS_CSV, sep=';', error_bad_lines=False)
  bids = pd.DataFrame(bids)
  summary = bids.merge(lookup, on='BID', how='left')
  summary.drop(inplace=True, 
    columns=['Year-Of-Publication', 'Publisher', 'Image-URL-S', 'Image-URL-M', 'Image-URL-L'])
  return summary

def recommend_books_by_author( aids ):
  lookup = pd.read_csv(BOOKS_CSV, sep=';', error_bad_lines=False)
  aids = pd.DataFrame(aids)
  summary = aids.merge(lookup, on='AID', how='left')
  return summary.BID

def lookup_authors( aids ):
  lookup = pd.read_csv(AUTHS_CSV, sep=',', error_bad_lines=False)
  aids = pd.DataFrame(aids)
  summary = aids.merge(lookup, on='AID', how='left')
  return summary

def get_user_ratings( user, ratings ):
  user_ratings = lookup_books(ratings[ratings.UID == user])
  return user_ratings

def recommend_books_by_item( user, model, ratings, thres=4.0, n=5 ):
  bids = ratings[(ratings.UID == user)]
  bids = bids[bids.Score >= thres].BID
  bids.reset_index(drop=True, inplace=True)

  result = []
  csr = books_to_csr(ratings)
  for i in range(bids.shape[0]):
    result = (model.similar_items(bids[i], N=n, react_users=csr.transpose()))
  result = [x for x,_ in result]
  result = pd.Series(result)
  result.name = 'BID'
  return 

def recommend_books_by_user( user, model, ratings, thres=4.0, n=5 ):
  ids_tuples = model.similar_users(user, n)
  ids = [x for x, _ in ids_tuples]

  bids = ratings[ratings.UID.isin(ids)]
  bids = bids[bids.Score >= thres].BID
  bids.reset_index(drop=True, inplace=True)

  return bids

def remove_already_read( user_ratings, bids ):
  bids = bids[~bids.isin(user_ratings.BID)]
  return bids

def score_by_book( user, model, ratings, bids ):
  csr = books_to_csr(ratings)
  scores = model.rank_items(user, csr, bids.to_list())
  scores = pd.DataFrame(scores, columns=['BID', 'BookScore'])

  return scores

def score_by_author( user, model, ratings, aids ):
  csr = authors_to_csr(ratings)
  scores = model.rank_items(user, csr, aids.to_list())
  scores = pd.DataFrame(scores, columns=['AID', 'AuthScore'])

  return scores

def rank_books( book_scores, auth_scores ):
  count = book_scores.groupby('BID').count()
  count.columns = ['Count']
  book_scores.drop_duplicates('BID', inplace=True)
  auth_scores.drop_duplicates('AID', inplace=True)

  ranking = lookup_books(book_scores)
  ranking = ranking.merge(auth_scores, on='AID', how='left')
  ranking = ranking.merge(count, on='BID', how='left')
  
  ranking['Overall'] = (0.05 * ranking['Count'] + ranking['BookScore'] + 0.05 * ranking['AuthScore']) 
  ranking = ranking[['BID', 'AID', 'ISBN', 'Book-Title', 'Book-Author', \
                     'Count', 'BookScore', 'AuthScore', 'Overall']]
  ranking.sort_values(['Count', 'BookScore'], ascending=False, inplace=True)
  ranking.reset_index(drop=True, inplace=True)
  return ranking



# Assemble a sparse matrix from a dataframe
def books_to_csr( ratings ):
  lookup = pd.read_csv(BOOKS_CSV, sep=';', error_bad_lines=False)

  n_users = ratings['UID'].nunique()
  n_books = lookup['BID'].nunique()

  data = ratings['Score']
  row_ind = ratings['UID']
  col_ind = ratings['BID']

  csr = csr_matrix((data, (row_ind, col_ind)), shape=(n_users, n_books))
  return csr

def authors_to_csr( ratings ):
  lookup = pd.read_csv(BOOKS_CSV, sep=';', error_bad_lines=False)

  n_users = ratings['UID'].nunique()
  n_auth = lookup['AID'].nunique()

  data = ratings['Score']
  row_ind = ratings['UID']
  col_ind = ratings['AID']

  csr = csr_matrix((data, (row_ind, col_ind)), shape=(n_users, n_auth))
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


def normalize_by_item_and_user( df ):
  df, mu_i = normalize_by_item(df)
  df, mu_u = normalize_by_user(df)
  return df, mu_i, mu_u

# For each rating, subtracts the average rating for the associated item (column).
# Returns the vector of averages for later prediction
def normalize_by_item( df ):
  csr = get_csr(df)

  sums = csr.sum(axis=0).flatten()
  counts = csr.getnnz(axis=0).flatten()
  mu = np.divide(sums, counts, out=np.zeros_like(sums), where=(counts != 0))
  mu = np.array(mu).flatten()

  df.Score -= mu[df.BID]
  return df, mu

# For each rating, subtracts the average rating from the associated user (row).
# Returns the vector of averages for later prediction
def normalize_by_user( df ):
  csr = get_csr(df)

  sums = csr.sum(axis=1).flatten()
  counts = csr.getnnz(axis=1).flatten()
  mu = np.divide(sums, counts, out=np.zeros_like(sums), where=(counts != 0))
  mu = np.array(mu).flatten()

  df.Score -= mu[df.UID]
  return df, mu

main()
