import numpy as np
import pandas as pd

def main():
  books = pd.read_csv('data/books.csv', sep=';', error_bad_lines=False)
  ratings = pd.read_csv('data/ratings.csv', sep=';')
  
  print(books.shape)
  print(ratings.shape)

main()