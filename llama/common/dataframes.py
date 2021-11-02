import numpy
import pandas
from scipy import stats

def df_complete_n_index(df, n, fill = 0):
  zeros = [fill for _ in range(n)]
  df_zero = pandas.DataFrame({k: zeros for k in df.columns}, index=[i for i in range(n)])
  return df.add(df_zero, fill_value=0)

def df_adjust_index(df, add, name=None):
  n = name or 'AdjustIndex'
  df[n] = df.index + add
  return df.set_index(n)

def df_adjust_index_to_zero(df, name=None):
  return df_complete_n_index(
    df_adjust_index(df, -numpy.min(df.index), name),
    numpy.max(df.index)
  )

def df_sum(to, series, name=None):
  n = name or series.name
  return to.add(series.to_frame(n), fill_value=0)

def df_index_sums(series, index, name=None):
  n = name or series.name
  return series.to_frame(n).join(index).groupby(index.name).sum()

def df_sum_by_index(to, series, index, name=None):
  return to.add(df_index_sums(series, index, name), fill_value=0)

def df_from_iterator(rows):
  df = pandas.DataFrame()
  for name, data in rows:
    df = df.append(pandas.Series(data, name=name))
  return df

def groupby_as_ones(groupby):
  return groupby.apply(lambda _: 1) if len(groupby) > 0 else pandas.Series()

def nth_delta(series, n=1):
  if series.shape[0] > n:
    return series.values[n] - series.values[n - 1]
  else:
    return numpy.nan

def as_minute_scalar(series):
  return series.astype('int64') // 1e9 / 60

def split_outliers(series, max_z_score=2.5):
  if series.empty:
    return series, pandas.Series()
  accept = numpy.abs(stats.zscore(series)) < max_z_score
  return series[accept], series[~accept]

def strip_outliers(series, max_z_score=2.5):
  accept, strip = split_outliers(series, max_z_score)
  if not strip.empty:
    print(f'Stripped outliers for "{series.name}"', strip.to_numpy())
  return accept

def zero_max_range(series):
  m = numpy.max(series)
  return (0, m if m > 0 else 1)

def zero_centered_range(series):
  m = numpy.max(series)
  return (-m, m) if m > 0 else (-1, 1)

def histogram_vals(series, select_range=None, n=5):
  if select_range is None:
    r = zero_max_range(series)
  elif hasattr(select_range, '__call__'):
    r = select_range(series)
  else:
    r = select_range
  if series.empty or ((series >= r[0]) & (series <= r[1])).sum() == 0:
    return [0 for _ in range(n)]
  return numpy.histogram(series, n, r, density=True)[0].tolist()

def sums_as_histogram_vals(series, n=7):
  vals = [0 for _ in range(n)]
  s = numpy.sum(series)
  d = series.shape[0] / n
  t = 0
  for i in range(series.shape[0]):
    if i >= (t + 1) * d:
      t += 1
    vals[t] += series[i] / s
  return vals

def write_or_print(df, csv_name=None):
  if csv_name:
    df.to_csv(csv_name)
  else:
    print(df)
