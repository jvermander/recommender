import numpy as np
import pandas as pd

import scipy.sparse as sps
from scipy.sparse import csr_matrix

def train_model( dbconn, path='data/models/impALS', f1=200, f2=200, l1=1, l2=1 ):
  query = 'SELECT * FROM bookratings;'
  bookratings = pd.read_sql(query, dbconn)

  query = 'SELECT * FROM authorratings;'
  authorratings = pd.read_sql(query, dbconn)

  model = implicit.als.AlternatingLeastSquares(iterations=5, factors=f1, regularization=l1, num_threads=4, calculate_training_loss=True)
  csr = books_to_csr(bookratings)
  model.fit(csr.transpose())
  pickle.dump(model, open(path + '/impALSbooks.sav', 'wb'))

  model = implicit.als.AlternatingLeastSquares(iterations=5, factors=f2, regularization=l2, num_threads=4, calculate_training_loss=True)
  csr = authors_to_csr(authorratings)
  model.fit(csr.transpose())
  pickle.dump(model, open(path + '/impALSauthors.sav', 'wb'))