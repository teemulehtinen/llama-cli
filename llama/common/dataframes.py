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

def write_or_print(df, csv_name=None):
  if csv_name:
    df.to_csv(csv_name)
  else:
    print(df)

def nth_delta(series, n=1):
  if series.shape[0] > n:
    return series.values[n] - series.values[n - 1]
  else:
    return numpy.nan

def groupby_ranges(groupby, key):
  vals = groupby[key].max() - groupby[key].min()
  return vals[vals > 0]

def groupby_nth_deltas(groupby, key, n=1):
  return groupby[key].apply(nth_delta, n=n).dropna()

def groupby_as_ones(groupby):
  return groupby.apply(lambda _: 1) if len(groupby) > 0 else pandas.Series()

def as_minute_scalar(series):
  return series.astype('int64') // 1e9 / 60

def split_outliers(series, max_z_score=2.5):
  if series.empty:
    return series, pandas.Series()
  accept = numpy.abs(stats.zscore(series)) < max_z_score
  return series[accept], series[~accept]

def strip_outliers(key, series, max_z_score=2.5):
  accept, strip = split_outliers(series, max_z_score)
  if not strip.empty:
    print(f'Stripped outliers for "{key}"', strip.to_numpy())
  return accept

def median_or_mean(series):
  m = numpy.median(series)
  return (numpy.mean(series), 'M') if numpy.isnan(m) else (m, 'Md')

def measures(series):
  if series is None:
    return None
  if series.empty:
    return {'n': 0, 'label': 'na', 'm': 0, 'mad': 0}
  m, label = median_or_mean(series)
  mad, _ = median_or_mean(numpy.absolute(series - m))
  return {'n': series.shape[0], 'label': label, 'm': m, 'mad': mad}

def sums_measures(series):
  if series is None:
    return None
  if series.empty:
    return {'n': 0, 'label': 'na', 'm': 0, 'mad': 0}
  n = numpy.sum(series)
  m = numpy.sum(i * series[i] for i in range(series.shape[0])) / n
  mad = numpy.sum(abs(i - m) * series[i] for i in range(series.shape[0])) / n
  return {'n': n, 'label': 'M', 'm': m, 'mad': mad}
