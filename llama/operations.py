from .config import TIME_KEY, PERSON_KEY

def last_time(rows):
  return rows[TIME_KEY].max()

def filter_to_last_by_person(rows):
  return rows\
    .sort_values(by=TIME_KEY)\
    .drop_duplicates(PERSON_KEY, keep='last', ignore_index=True)

def person_has_columns_value(rows, columns, value, reverse=False):
  for _, row in filter_to_last_by_person(rows).iterrows():
    has_value = all(row[c] == value for c in columns)
    yield row[PERSON_KEY], not has_value if reverse else has_value
