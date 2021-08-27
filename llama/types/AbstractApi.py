import io
import json
import requests
import pandas
from ..common import read_json, write_json, read_csv, write_csv

class AbstractApi:

  def list_tables(self, try_cache=True, only_cache=False):
    raise NotImplementedError()

  def fetch_rows(self, table, personal=False, only_cache=False):
    # Should optimize the queries to extend previous data, if possible.
    raise NotImplementedError()

  def get(self, url, headers={}):
    print(f'> GET {url}')
    return requests.get(url, headers=headers)

  def get_json(self, url):
    return json.loads(self.get(url).text)
  
  def get_csv(self, url):
    return pandas.read_csv(io.StringIO(self.get(url).text))

  def col_to_datetime(self, column):
    return pandas.to_datetime(column)
  
  def cached_json_or_get(self, getter, file_name, try_cache=True, only_cache=False):
    return self.cached_or_get(
      lambda: read_json(file_name),
      lambda: getter(),
      lambda r: write_json(file_name, r),
      try_cache,
      only_cache
    )

  def cached_csv_or_get(self, getter, file_name, try_cache=True, only_cache=False):
    return self.cached_or_get(
      lambda: read_csv(file_name),
      lambda: getter(),
      lambda r: write_csv(file_name, r),
      try_cache,
      only_cache
    )

  def cached_or_get(self, reader, getter, writer, try_cache=True, only_cache=False):
    if try_cache or only_cache:
      result = reader()
      if not result is None:
        return result, True
      elif only_cache:
        return None, False
    result = getter()
    writer(result)
    return result, False
