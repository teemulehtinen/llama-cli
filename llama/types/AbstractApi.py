import os
import time
import io
import json
import requests
import pandas
from ..Config import STORAGE_DIR, TIME_KEY, PERSON_KEY
from ..operations import ensure_column_types
from ..common import read_json, write_json, read_csv, write_csv, read_any, write_any

class AbstractApi:

  TABLE_LIST_JSON = '{source_id}-tables.json'
  TABLE_CSV = '{source_id}-{table_id}-rows.csv'
  TABLE_DIR = '{source_id}-{table_id}'
  ITEM_DIR = '{user_id}-{time}'
  META_JSON = 'meta.json'

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
  
  def fetch_rows(self, table, include_personal=False, only_cache=False, select_persons=None, exclude_columns=None):
    rows, cached = self.cached_csv_or_fetch(
      lambda: self.fetch_rows_csv(table, None, include_personal, select_persons, exclude_columns),
      self.table_csv_name(table['id']),
      True,
      only_cache
    )
    if cached:
      if not only_cache:
        new_rows = self.fetch_rows_csv(table, rows, include_personal, select_persons, exclude_columns)
        if not new_rows is None:
          write_csv(self.table_csv_name(table['id']), new_rows)
          rows = new_rows
          self.fetch_delay()
    else:
      self.fetch_delay()
    ensure_column_types(rows)
    return rows, cached

  def fetch_files(self, table, rows, include_personal=False, only_cache=False):
    file_cols = self.file_columns(table, rows)
    table_dir = self.table_dir_name(table['id'])
    for _, row in rows.iterrows():
      item_dir = self.item_dir_name(row)
      for c in file_cols:
        path = (STORAGE_DIR, table_dir, item_dir, c)
        content, cached = self.cached_or_fetch(
          lambda: read_any(path),
          lambda: self.fetch_file(table, row, c, include_personal),
          lambda r: write_any(path, r),
          True,
          only_cache
        )
        if not content is None and not cached:
          self.fetch_delay()
        yield { 'row': row, 'col': c, 'path': path, 'content': content, 'cached': cached }

  def fetch_meta(self, table, rows, include_personal=False, only_cache=False):
    table_dir = self.table_dir_name(table['id'])
    for _, row in rows.iterrows():
      item_dir = self.item_dir_name(row)
      path = (STORAGE_DIR, table_dir, item_dir, self.META_JSON)
      content, cached = self.cached_json_or_fetch(
        lambda: self.fetch_meta_json(table, row, include_personal),
        path,
        True,
        only_cache
      )
      if not content is None and not cached:
        self.fetch_delay()
      yield { 'row': row, 'path': path, 'content': content, 'cached': cached }

  def export_rows(self, table, rows, person_map, metas=False, volatile_columns=None):
    data = self.drop_for_export(table, rows, volatile_columns)
    data[PERSON_KEY] = data[PERSON_KEY].map(person_map)
    data = data.dropna(subset=[PERSON_KEY]).reset_index(drop=True)
    table_dir = self.table_dir_name(table['id'])
    file_cols = self.file_columns(table, rows)
    def rewrite_files(row):
      item_dir = self.item_dir_name(row)
      for c in file_cols:
        row[c] = os.path.join(table_dir, item_dir, c)
      return row
    data = data.apply(rewrite_files, 1)
    if metas:
      data['RowMeta'] = [
        os.path.join(table_dir, self.item_dir_name(row), self.META_JSON)
        for _, row in data.iterrows()
      ]
    return data

  def fetch_tables_json(self):
    raise NotImplementedError()

  def fetch_rows_csv(self, table, old_rows, include_personal, select_persons, exclude_columns):
    # MUST use default keys if appropriate columns: TIME_KEY, PERSON_KEY, GRADE_KEY
    # Should optimize the queries to extend previous data, if possible.
    raise NotImplementedError()
  
  def fetch_meta_json(self, table, row, include_personal):
    raise NotImplementedError()

  def file_columns(self, table, rows):
    raise NotImplementedError()

  def fetch_file(self, table, row, col_name, include_personal):
    raise NotImplementedError()

  def drop_for_export(self, table, rows):
    raise NotImplementedError()

  def table_list_json_name(self):
    return (
      self.TABLE_LIST_JSON.format(source_id=self.source_id),
    )

  def table_csv_name(self, table_id):
    return (
      STORAGE_DIR,
      self.TABLE_CSV.format(source_id=self.source_id, table_id=table_id),
    )

  def table_dir_name(self, table_id):
    return self.TABLE_DIR.format(source_id=self.source_id, table_id=table_id)

  def item_dir_name(self, row):
    return self.ITEM_DIR.format(
      user_id=row[PERSON_KEY],
      time=row[TIME_KEY].strftime(r'%Y%m%d%H%M%S')
    )

  def fetch_delay(self):
    time.sleep(self.REQUEST_DELAY)

  def fetch(self, url, headers={}):
    print(f'> GET {url}')
    return requests.get(url, headers=headers)

  def fetch_json(self, url):
    return json.loads(self.fetch(url).text)
  
  def fetch_csv(self, url):
    return pandas.read_csv(io.StringIO(self.fetch(url).text))

  def cached_json_or_fetch(self, fetch, path, try_cache=True, only_cache=False):
    return self.cached_or_fetch(
      lambda: read_json(path),
      lambda: fetch(),
      lambda r: write_json(path, r),
      try_cache,
      only_cache
    )

  def cached_csv_or_fetch(self, fetch, path, try_cache=True, only_cache=False):
    return self.cached_or_fetch(
      lambda: read_csv(path),
      lambda: fetch(),
      lambda r: write_csv(path, r),
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
    if not result is None:
      write(result)
    return result, False
