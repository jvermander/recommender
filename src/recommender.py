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
  # cross_val(df)
  # model, mu = train_model('models/ALS', df.copy())
  model, mu = load_model('models/ALS')
  predict(model, df, mu)

def train_model( path, df ):
  os.environ["PYSPARK_PYTHON"]="/usr/bin/python3.5"
  ps = SparkSession.builder.master("local[4]").appName('Recommender').getOrCreate()
  
  df, mu = normalize_by_item(df)
  df = ps.createDataFrame(df)
  als = ALS(userCol='UID', itemCol='BID', ratingCol='Score', coldStartStrategy='drop',
            maxIter=15, rank=20, regParam=0.3)
  model = als.fit(df)
  model.write().overwrite().save(path)
  np.save(path + '/mu_item.npy', mu)
  # np.save(path + '/mu_user.npy', mu_u)
  return model, mu

def load_model( path ):
  os.environ["PYSPARK_PYTHON"]="/usr/bin/python3.5"
  ps = SparkSession.builder.master("local[4]").appName('Recommender').getOrCreate()

  model = ALSModel.load(path)
  mu_i = np.load(path + '/mu_item.npy')
  # mu_u = np.load(path + '/mu_user.npy')

  return model, mu_i#, mu_u

def predict( model, df, mu ):
  user = df.UID.nunique()-1
  print(user)
  lookup = pd.read_csv(BOOKS_CSV, sep=';', error_bad_lines=False)
  
  item_counts = df.groupby('BID').nunique()
  item_counts = item_counts[item_counts.UID >= 1]
  item_counts = item_counts.index
  print(item_counts)

  print(df)
  user_df = df[df.UID == user].merge(lookup, on='BID', how='left')
  user_df = user_df.loc[:, ['BID', 'ISBN', 'Book-Title', 'Book-Author', 'Score']]
  print(user_df)

  item_matrix = model.itemFactors.toPandas()
  item_features = np.stack(item_matrix.features)

  
  user_matrix = model.userFactors.toPandas()
  user_features = np.stack(user_matrix.features)


  user_vec = user_matrix[user_matrix.id == user].features
  user_vec = np.stack(user_vec)

  print("Results:")
  csr = get_csr(df)

  nn = NearestNeighbors(n_neighbors=3)
  nn.fit(csr)
  idx = nn.kneighbors(csr[user, :], return_distance=False)[0]

  print(idx)

  sim = df[df.UID.isin(idx)].merge(lookup, on='BID', how='left')
  sim = sim.loc[:, ['UID', 'BID', 'ISBN', 'Book-Title', 'Book-Author', 'Score']]
  print(sim.sort_values('UID'))

  # What is the prediction for each BID on the similarity list? Sort, then recommend


  p = np.dot(item_features, user_vec.reshape(-1))

  p = pd.DataFrame(p)
  p.columns = ['Prediction']
  p = pd.concat([item_matrix, p], axis=1)
  p.sort_values('Prediction', axis=0, ascending=False, inplace=True)


  # p = p[p.id.isin(item_counts)]
  # p = p.iloc[:20, :]
  p.reset_index(drop=True, inplace=True)
  # p.Prediction += mu_u[user]
  # p.Prediction += mu_i[item_matrix.id]
  print(p)

  p.rename(columns={'id': 'BID'}, inplace=True)
  p = p.merge(lookup, on='BID', how='left')
  p = p.loc[:, ['BID', 'ISBN', 'Book-Title', 'Book-Author', 'Prediction']]
  p.Prediction += mu[p.BID]
  p.sort_values('Prediction', axis=0, ascending=False, inplace=True)
  p.reset_index(drop=True, inplace=True)


  print(p.iloc[:10, :])
  print(p[p.BID == 2809])
  print(p[p.BID.isin(user_df.BID)])

# Tunes hyperparameters and evaluates the model building process
def cross_val( df ):
  df, mu_i = normalize_by_item(df)
  os.environ["PYSPARK_PYTHON"]="/usr/bin/python3.5"
  ps = SparkSession.builder.master("local[4]").appName('Recommender').getOrCreate()
  x = ps.createDataFrame(df)
  outer_train, outer_test = x.randomSplit([0.95, 0.05])
  als = ALS(userCol='UID', 
            itemCol='BID', 
            ratingCol='Score', 
            coldStartStrategy='drop',
            maxIter=15)
  grid = ParamGridBuilder().addGrid(als.rank, [20],) \
                           .addGrid(als.regParam, [0.3]).build()
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
