import os
import time
import io
import json
import requests
import pandas
from ..common import read_json, write_json, read_csv, write_csv, read_text, ensure_dir_and_write_text

class AbstractApi:

  TABLE_LIST_JSON = '{source_id}-tables.json'
  TABLE_CSV = '{source_id}-{table_id}-rows.csv'
  TABLE_DIR = '{source_id}-{table_id}'
  ITEM_DIR = '{user_id}-{time}'

  REQUEST_DELAY = 1 #sec

  def __init__(self, source_id):
    self.source_id = source_id

  def list_tables(self, try_cache=True, only_cache=False):
    return self.cached_json_or_fetch(
      lambda: self.fetch_tables_json(),
      self.table_list_json_name(),
      try_cache,
      only_cache
    )

  def fetch_rows(self, table, include_personal=False, only_cache=False):
    rows, cached = self.cached_csv_or_fetch(
      lambda: self.fetch_rows_csv(table, None, include_personal),
      self.table_csv_name(table['id']),
      True,
      only_cache
    )
    if cached:
      rows = self.pass_cached_rows_csv(rows)
      if not only_cache:
        rows = self.fetch_rows_csv(table, rows, include_personal)
    else:
      self.fetch_delay()
    return rows, cached

  def fetch_files(self, table, include_personal=False, only_cache=False):
    rows, _ = self.fetch_rows(table, include_personal, True)
    if rows is None:
      print(f'Skipping {table["name"]}: fetch rows first')
    else:
      file_cols = self.file_columns(table, rows)
      table_dir = self.table_dir_name(table['id'])
      for _, row in rows.iterrows():
        item_dir = self.item_dir_name(row)
        for c in file_cols:
          content, cached = self.cached_or_fetch(
            lambda: read_text(os.path.join(table_dir, item_dir, c)),
            lambda: self.fetch_file(table, row, c, include_personal),
            lambda r: ensure_dir_and_write_text([table_dir, item_dir, c], r),
            True,
            only_cache
          )
          if not cached:
            self.fetch_delay()
          yield { 'row': row, 'col': c, 'content': content, 'cached': cached }


  def fetch_tables_json(self):
    raise NotImplementedError()

  def fetch_rows_csv(self, table, old_rows, include_personal):
    # Should optimize the queries to extend previous data, if possible.
    raise NotImplementedError()
  
  def pass_cached_rows_csv(self, data):
    return data

  def file_columns(self, table, rows):
    raise NotImplementedError()

  def fetch_file(self, table, row, col_name, include_personal):
    raise NotImplementedError()

  def item_dir_name(self, row):
    raise NotImplementedError()


  def table_list_json_name(self):
    return self.TABLE_LIST_JSON.format(source_id=self.source_id)

  def table_csv_name(self, table_id):
    return self.TABLE_CSV.format(source_id=self.source_id, table_id=table_id)

  def table_dir_name(self, table_id):
    return self.TABLE_DIR.format(source_id=self.source_id, table_id=table_id)


  def fetch_delay(self):
    time.sleep(self.REQUEST_DELAY)

  def fetch(self, url, headers={}):
    print(f'> GET {url}')
    return requests.get(url, headers=headers)

  def fetch_json(self, url):
    return json.loads(self.fetch(url).text)
  
  def fetch_csv(self, url):
    return pandas.read_csv(io.StringIO(self.fetch(url).text))

  def col_to_datetime(self, column):
    return pandas.to_datetime(column)
  
  def cached_json_or_fetch(self, fetch, file_name, try_cache=True, only_cache=False):
    return self.cached_or_fetch(
      lambda: read_json(file_name),
      lambda: fetch(),
      lambda r: write_json(file_name, r),
      try_cache,
      only_cache
    )

  def cached_csv_or_fetch(self, fetch, file_name, try_cache=True, only_cache=False):
    return self.cached_or_fetch(
      lambda: read_csv(file_name),
      lambda: fetch(),
      lambda r: write_csv(file_name, r),
      try_cache,
      only_cache
    )
  
  def cached_or_fetch(self, read, fetch, write, try_cache=True, only_cache=False):
    if try_cache or only_cache:
      result = read()
      if not result is None:
        return result, True
      elif only_cache:
        return None, False
    result = fetch()
    write(result)
    return result, False
