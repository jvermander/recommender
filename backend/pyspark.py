import pyspark
from pyspark.sql import SparkSession
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS, ALSModel
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder, CrossValidatorModel

def train_model( path, df, offset ):
  os.environ["PYSPARK_PYTHON"]="/usr/bin/python3.5"
  ps = SparkSession.builder.master("local[4]").appName('Recommender').getOrCreate()
  
  df, mu_i = normalize_by_item(df)
  mu_u = None
  if(offset):
    df, mu_u = normalize_by_user(df)
  df = ps.createDataFrame(df)
  als = ALS(userCol='UID', itemCol='BID', ratingCol='Score', coldStartStrategy='drop',
            maxIter=15, rank=20, regParam=0.3)
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