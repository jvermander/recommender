# Book recommender system:
# Matrix Factorization via Alternating Least Squares

import numpy as np
import pandas as pd

import scipy.sparse as sps
from scipy.sparse import csr_matrix

import pyspark
from pyspark.sql import SparkSession
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS, ALSModel
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder, CrossValidatorModel

from sklearn.model_selection import GridSearchCV, cross_val_score, KFold, StratifiedKFold, RandomizedSearchCV
from sklearn.neighbors import NearestNeighbors

import csv
import time
import os
import glob


TRAIN_DIR = 'data/train_x'
BOOKS_CSV = 'data/lookup.csv'

def main():

  # data = pd.read_csv('data/out.csv')

  # by_item = data.groupby('BID')['UID'].nunique()
  # by_item = by_item[by_item >= 5]
  # print(by_item)

  # data = data[data.BID.isin(by_item.index)]
  # print(data.nunique())

  # data = lower_bound_ratings(data, 10, 'data/b5u10.csv')

  # print(data.nunique())

  # print(data)


  files = glob.glob(TRAIN_DIR + '/*.csv')
  df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
  # cross_val(df.copy())
  train_model('models/ALS', df.copy(), offset=True)
  model, mu_i, mu_u = load_model('models/ALS')
  recommend(model, df, mu_i, mu_u)

def train_model( path, df, offset ):
  os.environ["PYSPARK_PYTHON"]="/usr/bin/python3.5"
  ps = SparkSession.builder.master("local[4]").appName('Recommender').getOrCreate()
  
  df, mu_i = normalize_by_item(df)
  mu_u = None
  if(offset):
    df, mu_u = normalize_by_user(df)
  df = ps.createDataFrame(df)
  als = ALS(userCol='UID', itemCol='BID', ratingCol='Score', coldStartStrategy='drop',
            maxIter=15, rank=30, regParam=0.3)
  model = als.fit(df)
  model.write().overwrite().save(path)
  np.save(path + '/mu_item.npy', mu_i)
  if(offset):
    np.save(path + '/mu_user.npy', mu_u)
  return model, mu_i, mu_u

def load_model( path ):
  os.environ["PYSPARK_PYTHON"]="/usr/bin/python3.5"
  ps = SparkSession.builder.master("local[4]").appName('Recommender').getOrCreate()

  model = ALSModel.load(path)
  mu_i = np.load(path + '/mu_item.npy')
  try:
    mu_u = np.load(path + '/mu_user.npy')
  except:
    mu_u = None
  return model, mu_i, mu_u

def lookup( ratings, labels=['UID', 'BID', 'ISBN', 'Book-Title', 'Book-Author', 'Score'] ):
  lookup = pd.read_csv(BOOKS_CSV, sep=';', error_bad_lines=False)
  ratings = ratings.merge(lookup, on='BID', how='left')
  ratings = ratings.loc[:, labels]
  return ratings

def get_user_ratings( user, ratings ):
  user_ratings = lookup(ratings[ratings.UID == user])
  return user_ratings

def get_similar_user_ratings( user, ratings, n=5 ):
  csr = get_csr(ratings)
  nn = NearestNeighbors(n_neighbors=n+1, algorithm='brute', metric='manhattan')
  nn.fit(csr)
  ids = nn.kneighbors(csr[user, :], return_distance=False)[0][1:]
  print(ids)
  sim = lookup(ratings[ratings.UID.isin(ids)])

  return sim

def predict( user_vector, items_pd, mu_i, user_offset=0 ):
  items_np = np.stack(items_pd.features)
  user_vector = user_vector.reshape(-1)
  p = pd.DataFrame(np.dot(items_np, user_vector))
  p.columns = ['Predicted']
  p = pd.concat([items_pd.reset_index(drop=True), p.reset_index(drop=True)], axis=1)
  p.rename(columns={'id': 'BID'}, inplace=True)
  p = lookup(p, ['BID', 'ISBN', 'Book-Title', 'Book-Author', 'Predicted'])
  p.Predicted += mu_i[p.BID] + user_offset
  p.sort_values('Predicted', axis=0, ascending=False, inplace=True)
  p.reset_index(drop=True, inplace=True)
  return p

# todo: sophisticate user-user similarity, implement item-item similarity
def recommend( model, ratings, mu_i, mu_u=None ):
  user = ratings.UID.nunique()-3
  lookup = pd.read_csv(BOOKS_CSV, sep=';', error_bad_lines=False)

  print(user)
  user_ratings = get_user_ratings(user, ratings)
  print(user_ratings)

  similar_ratings = get_similar_user_ratings(user, ratings, 5)
  print(similar_ratings)

  items_pd = model.itemFactors.toPandas()
  users_pd = model.userFactors.toPandas()
  user_vec = np.stack(users_pd[users_pd.id == user].features)
 

  similar_pd = items_pd[items_pd.id.isin(similar_ratings.BID)]
  user_offset = 0
  if(mu_u is not None):
    user_offset = mu_u[user]
  similar_predictions = predict(user_vec, similar_pd, mu_i, user_offset)
  print(similar_predictions[~similar_predictions.BID.isin(user_ratings.BID)])

  p = predict(user_vec, items_pd, mu_i, user_offset)
  # print(p.iloc[:10, :])
  # print(p[p.BID == 2809])
  print(p[p.BID.isin(user_ratings.BID)])

# Tunes hyperparameters and evaluates the model building process
def cross_val( df ):
  df, mu_i, mu_u = normalize_by_item_and_user(df)
  os.environ["PYSPARK_PYTHON"]="/usr/bin/python3.5"
  ps = SparkSession.builder.master("local[4]").appName('Recommender').getOrCreate()
  x = ps.createDataFrame(df)
  outer_train, outer_test = x.randomSplit([0.95, 0.05])
  als = ALS(userCol='UID', 
            itemCol='BID', 
            ratingCol='Score', 
            coldStartStrategy='drop',
            maxIter=15)
  grid = ParamGridBuilder().addGrid(als.rank, [10, 20, 30],) \
                           .addGrid(als.regParam, [0.3, 0.6]).build()
  evaluator = RegressionEvaluator(metricName='rmse', 
                                 labelCol='Score', 
                                 predictionCol='prediction')
  inner_cv = CrossValidator(estimator=als, 
                            estimatorParamMaps=grid, 
                            evaluator=evaluator,
                            numFolds=3,
                            seed=1)

  cv_model = inner_cv.fit(outer_train)

  scores = cv_model.avgMetrics
  print(scores)
  for i in range(len(scores)):
    print(grid[i].values(), scores[i])

  predictions = cv_model.transform(outer_test)
  rmse = evaluator.evaluate(predictions)
  print("Outer: %.3f" % (float(rmse)))

  predictions = predictions.toPandas()
  outer_test = outer_test.toPandas()
  print("Cold Start - Predicted %d out of %d - %.3f" 
    % (predictions.shape[0], outer_test.shape[0], predictions.shape[0] / outer_test.shape[0]))

  predictions_train = cv_model.transform(outer_train)
  rmse = evaluator.evaluate(predictions_train)
  print("Train: %.3f" % (float(rmse)))

  return predictions

# Assemble a sparse matrix from a dataframe
def get_csr( ratings ):
  lookup = pd.read_csv(BOOKS_CSV, sep=';', error_bad_lines=False)

  n_users = ratings['UID'].nunique()
  n_books = lookup['BID'].nunique()

  data = ratings['Score']
  row_ind = ratings['UID']
  col_ind = ratings['BID']

  csr = csr_matrix((data, (row_ind, col_ind)), shape=(n_users, n_books))
  return csr

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




main()
