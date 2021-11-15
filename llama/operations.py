import pandas
from .common import df_accepted, groupby_ranges, groupby_nth_deltas
from .Config import TIME_KEY, PERSON_KEY

WEEKDAY_KEY = 'Weekday'
WEEKNUMBER_KEY = 'Weeknumber'
HOUR_KEY = 'Hour'

def parse_timecolumn(rows):
  if not rows is None and TIME_KEY in rows:
    rows[TIME_KEY] = pandas.to_datetime(rows[TIME_KEY])

def last_time(rows):
  return rows[TIME_KEY].max()

def filter_by_person(rows, included=None, excluded=None):
  return pandas.DataFrame(df_accepted(rows, PERSON_KEY, included, excluded))

def filter_to_last_by_person(rows):
  return rows\
    .sort_values(by=TIME_KEY)\
    .drop_duplicates(PERSON_KEY, keep='last', ignore_index=True)

def person_has_columns_value(rows, columns, value, reverse=False):
  for _, row in filter_to_last_by_person(rows).iterrows():
    has_value = all(row[c['key']] == value for c in columns)
    yield row[PERSON_KEY], not has_value if reverse else has_value

def append_discrete_time_columns(rows):
  rows[WEEKDAY_KEY] = rows[TIME_KEY].dt.dayofweek
  rows[WEEKNUMBER_KEY] = rows[TIME_KEY].dt.weekofyear
  rows[HOUR_KEY] = rows[TIME_KEY].dt.hour

def times_until_end(groupby):
  return groupby_ranges(groupby, TIME_KEY)

def times_nth_delta(groupby, n=1):
  return groupby_nth_deltas(groupby, TIME_KEY, n)
