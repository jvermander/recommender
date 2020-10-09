# Scratch implementation of stochastic gradient descent for matrix factorization

from sklearn.linear_model import SGDRegressor
from sklearn.utils.testing import ignore_warnings
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import train_test_split

NUM_USERS = 12791
NUM_BOOKS = 271378

#todo: parallelize
@ignore_warnings(category=ConvergenceWarning)
def SGD( df, epoch=5, k=200, l=0.001 ):
  train, test = train_test_split(df, test_size=0.05, random_state=1)
  
  print(train)
  users = train.UID.reset_index(drop=True)
  books = train.BID.reset_index(drop=True)
  ratings = train.Score.reset_index(drop=True)
  
  # print(users.shape, books.shape, ratings.shape)
  # for i in np.random.randint(low=0, high=ratings.shape[0], size=(5,)):
  #   print(users[i], books[i], ratings[i])

  np.random.seed(1)

  # U = np.load('matrices/U2.npy')
  # V = np.load('matrices/V2.npy')
  U = np.random.uniform(low=-1, high=1, size=(NUM_USERS, k))
  V = np.random.uniform(low=-1, high=1, size=(NUM_BOOKS, k))

  descent = SGDRegressor(max_iter=1, fit_intercept=False, alpha=l)
  for i in range(epoch):
    rmse = calc_rmse(U, V, ratings, users, books)
    print('Starting Epoch %d with RMSE = %.3f' % (i, rmse))
    print('Test RSME = %.3f' % calc_rmse_cold_start(U, V, ratings, users, books, test))

    idx = np.array(range(ratings.shape[0]))
    idx = np.random.permutation(idx)

    for j in idx:
      user_vector = U[users[j], :]
      book_vector = V[books[j], :]
      y = np.array(ratings[j]).reshape(1,)

      descent.fit(X=book_vector.reshape(1, k), y=y, coef_init=user_vector)
      U[users[j], :] = descent.coef_
      
      descent.fit(X=user_vector.reshape(1, k), y=y, coef_init=book_vector)
      V[books[j], :] = descent.coef_

    np.save('matrices/U2.npy', U)
    np.save('matrices/V2.npy', V)

  print('Completed with RSME = %.3f.' % calc_rmse(U, V, ratings, users, books))
  print('Test RSME = %.3f' % calc_rmse_cold_start(U, V, train, test))


def calc_rmse(U, V, ratings, users, books):
  sum = 0
  for i in range(ratings.shape[0]):
    sum += (np.dot(U[users[i], :], V[books[i], :]) - ratings[i]) ** 2
  
  rmse = np.sqrt(sum / ratings.shape[0])
  return rmse    

def calc_rmse_cold_start(U, V, ratings_train, users_train, books_train, test):
  users_test = test.UID.reset_index(drop=True)
  books_test = test.BID.reset_index(drop=True)
  ratings_test = test.Score.reset_index(drop=True)

  sum = 0
  n = 0
  for i in range(ratings_test.shape[0]):
    if(users_test[i] in users_train and books_test[i] in books_train):
      sum += (np.dot(U[users_test[i], :], V[books_test[i], :]) - ratings_test[i]) ** 2
      # print('%d,%d,%.1f,%.3f' %(users_test[i], books_test[i], ratings_test[i], np.dot(U[users_test[i], :], V[books_test[i], :])))
      n += 1
  
  assert(n > 0)
  print('In test RSME, processed %d out of %d ratings.' %(n, ratings_test.shape[0]))
  rmse = np.sqrt(sum / n)
  return rmse