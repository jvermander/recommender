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

import csv
import time
import os
import glob

TRAIN_DIR = 'data/train10'
BOOKS_CSV = 'data/booksdataset.csv'
AUTHS_CSV = 'data/authsdataset.csv'

user = 6589
def main():
  # files = glob.glob(TRAIN_DIR + '/*.csv')
  # df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
  # df.sort_values('UID', inplace=True)
  # df.reset_index(drop=True, inplace=True)
  
  # df = pd.DataFrame(df.groupby(['UID', 'AID']).Score.mean())
  # df.reset_index(inplace=True)
  # df.rename(columns={'AID':'BID'}, inplace=True)
  # df.to_csv(TRAIN_DIR + 'authors10.csv', index=False, quoting=csv.QUOTE_NONNUMERIC)

  books = pd.read_csv(TRAIN_DIR + '/books10.csv')
  auths = pd.read_csv(TRAIN_DIR + '/authors10.csv')

  path = 'models/impALS'
  # # train_model(books, auths, path)
  book_model, auth_model = load_model(path)
  recommend(books, auths, book_model, auth_model)

def train_model( books, authors, path, f=200, l=0.3 ):


  model = implicit.als.AlternatingLeastSquares(factors=f, regularization=l, num_threads=4)
  csr = books_to_csr(books)
  model.fit(csr.transpose())
  pickle.dump(model, open(path + '/impALSbooks.sav', 'wb'))

  model = implicit.als.AlternatingLeastSquares(factors=f, regularization=l, num_threads=4)
  csr = authors_to_csr(authors)
  model.fit(csr.transpose())
  pickle.dump(model, open(path + '/impALSauthors.sav', 'wb'))

def load_model( path ):
  book_model = pickle.load(open(path + '/impALSbooks.sav', 'rb'))
  auth_model = pickle.load(open(path + '/impALSauthors.sav', 'rb'))
  
  return book_model, auth_model

# todo: finish author recommendations, consolidate data, clean-up

def recommend( books, auths, book_model, auth_model ):
  global user

  print('UID ', user)
  user_ratings = get_user_ratings(user, books)
  print(user_ratings)

  # 1) user-user similarity
  # 2) item-item similarity
  # 3) rank by book score, author score, frequency

  candidates = pd.Series(name='BID')
  candidates = candidates.append(recommend_by_book(user, book_model, books))
  candidates = candidates.append(recommend_by_user(user, book_model, books))
  candidates = remove_already_read(user_ratings, candidates)

  book_scores = score_by_book(user, book_model, books, candidates)
  aids = lookup_books(candidates).AID
  auth_scores = score_by_author(user, auth_model, auths, aids)

  ranking = rank_books(book_scores, auth_scores)
  ranking.sort_values(['Count', 'Overall'], ascending=False, inplace=True)
  # ranking = filter_ranking(ranking)

  print(ranking[:30])


  aids = recommend_by_author(user, auth_model, auths).sort_values('AuthScore', ascending=False)
  author_ranking = lookup_authors(aids)
  author_ranking.drop_duplicates('AID', inplace=True)
  print(author_ranking)


def lookup_books( bids ):
  lookup = pd.read_csv(BOOKS_CSV, sep=';', error_bad_lines=False)
  bids = pd.DataFrame(bids)
  summary = bids.merge(lookup, on='BID', how='left')
  summary.drop(inplace=True, 
    columns=['Year-Of-Publication', 'Publisher', 'Image-URL-S', 'Image-URL-M', 'Image-URL-L'])
  return summary

def lookup_authors( aids ):
  lookup = pd.read_csv(AUTHS_CSV, sep=',', error_bad_lines=False)
  aids = pd.DataFrame(aids)
  summary = aids.merge(lookup, on='AID', how='left')
  return summary

def get_user_ratings( user, ratings ):
  user_ratings = lookup_books(ratings[ratings.UID == user])
  return user_ratings

def recommend_by_book( user, model, ratings, thres=4.0, n=5 ):
  bids = ratings[(ratings.UID == user)]
  bids = bids[bids.Score >= thres].BID
  bids.reset_index(drop=True, inplace=True)

  result = []
  csr = books_to_csr(ratings)
  for i in range(bids.shape[0]):
    result += (model.similar_items(bids[i], N=n, react_users=csr.transpose()))
  result = [x for x,_ in result]
  result = pd.Series(result)
  result.name = 'BID'
  return result

def recommend_by_user( user, model, ratings, thres=4.0, n=5 ):
  ids_tuples = model.similar_users(user, n)
  ids = [x for x, _ in ids_tuples]

  bids = ratings[ratings.UID.isin(ids)]
  bids = bids[bids.Score >= thres].BID
  bids.reset_index(drop=True, inplace=True)

  return bids

#todo
def recommend_by_author( user, model, ratings, thres=4.0, n=5 ):
  aids = ratings[(ratings.UID == user)]
  aids = aids[aids.Score >= thres].AID
  aids.reset_index(drop=True, inplace=True)

  result = []
  csr = authors_to_csr(ratings)
  for i in range(aids.shape[0]):
    result += (model.similar_items(aids[i], N=n, react_users=csr.transpose()))
  # result = [x for x,_ in result]
  result = pd.DataFrame(result)
  result.columns = ['AID', 'AuthScore']
  return result


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
  
  ranking['Overall'] = ranking['BookScore'] + 1.2 * ranking['AuthScore']
  ranking = ranking[['BID', 'AID', 'ISBN', 'Book-Title', 'Book-Author', \
                     'Count', 'BookScore', 'AuthScore', 'Overall']]
  return ranking

# def filter_ranking( ranking ):
#   ranking = ranking[ranking.Overall >= 0.03]


def get_similar_users( user, ratings, n=5 ):
  liked = ratings.Score >= 4.0
  # ratings.loc[liked, 'Score'] = 1
  ratings.loc[~liked, 'Score'] = 0

  csr = get_csr(ratings)
  similarities = pd.Series(cosine_similarity(csr, csr[user, :]).reshape(-1))
  similarities.sort_values(ascending=False, inplace=True)
  ids = similarities.index[1:1+n]

  return ids

def get_similar_user_ratings( user, ratings, n=5 ):
  ids = get_similar_users(user, ratings, n)
  sim = lookup_books(ratings[ratings.UID.isin(ids)])

  return sim.BID



def get_similar_items( user_ratings, ratings, thres=4.0, n_similar=5 ):
  # user_ratings.sort_values('Score', ascending=False, inplace=True)
  top_ratings = user_ratings[user_ratings.Score >= thres]
  csr = get_csr(ratings).transpose()
  similarities = pd.DataFrame(cosine_similarity(csr, csr[top_ratings.BID]))

  ids = np.argpartition(np.array(similarities), kth=-n_similar, axis=0)[-n_similar:]
  ids = pd.DataFrame(ids.flatten())
  ids.columns = ['BID']
  ids = ids[~ids.BID.isin(user_ratings.BID)]
  items = lookup_books(ids, ['BID', 'ISBN', 'Book-Title', 'Book-Author'])

  counts = pd.DataFrame(items.groupby('BID').count().iloc[:, 0])
  counts.columns = ['Count']
  # items = items.merge(counts, on='BID', how='left')
  items.drop_duplicates('BID', inplace=True)
  # items.sort_values('Count', inplace=True, ascending=False)

  return items.BID

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
