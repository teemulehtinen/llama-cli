import pandas

def ser_concat(*series):
  return pandas.concat(series, ignore_index=True)
