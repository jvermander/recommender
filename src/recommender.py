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

import csv
import time
import os
import glob

os.environ["PYSPARK_PYTHON"]="/usr/bin/python3.5"
ps = SparkSession.builder.master("local[4]").appName('Recommender').getOrCreate()

TRAIN_DIR = 'data/train'
RATINGS_CSV = 'data/out5.csv'
BOOKS_CSV = 'data/lookup.csv'

def main():
  train_model('models/ALS')

def train_model( path, new_csv=None ):
  files = glob.glob(TRAIN_DIR + '/*.csv')
  df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)

  df = ps.createDataFrame(df)
  als = ALS(userCol='UID', itemCol='BID', ratingCol='Score', coldStartStrategy='drop',
            maxIter=15, rank=10, regParam=0.5)
  model = als.fit(df)
  model.write().overwrite().save(path)

def predict():
  pass

# Tunes hyperparameters and evaluates the model building process
def cross_val( df ):
  global ps
  x = ps.createDataFrame(df)
  outer_train, outer_test = x.randomSplit([0.95, 0.05])
  als = ALS(userCol='UID', 
            itemCol='BID', 
            ratingCol='Score', 
            coldStartStrategy='drop',
            maxIter=15)
  grid = ParamGridBuilder().addGrid(als.rank, [10, 20, 50],) \
                           .addGrid(als.regParam, [0.3, 0.5, 1]).build()
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
def get_csr( ratings=None ):
  lookup = pd.read_csv(BOOKS_CSV, sep=';', error_bad_lines=False)
  if(ratings is None):
    ratings = pd.read_csv(RATINGS_CSV, sep=',')

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


main()
