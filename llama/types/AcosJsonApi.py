import os
import re
import json
import datetime
import pandas
from .AbstractApi import AbstractApi
from ..Config import TIME_KEY, GRADE_KEY, PERSON_KEY

class AcosJsonApi(AbstractApi):

  @classmethod
  def create(cls, source_id, directory):
    return AcosJsonApi(source_id, directory)

  def __init__(self, source_id, directory):
    super().__init__(source_id)
    self.dir = directory
    self.log_name_re = re.compile('^(\w+)_\d{6}-\d{6}.log$')

  def fetch_tables_json(self):
    tables = []
    with os.scandir(self.dir) as d:
      for f in [e.name for e in d if e.is_file()]:
        m = self.log_name_re.search(f)
        if not m is None:
          tables.append({
            'module_id': None,
            'module_name': None,
            'id': m.group(1),
            'name': m.group(1),
            'log_file': os.path.join(self.dir, f),
            'max_points': None,
            'max_submissions': None,
            'columns': [{ 'key': 'log' }],
          })
    return tables

  def fetch_rows_csv(self, table, old_rows, include_personal, select_persons, exclude_columns):

    # NOTE: no use to extend previously fetched rows from complete log dump
    if not old_rows is None:
      print(f'* Cached {table["name"]}: to update, remove {os.path.join(*self.table_csv_name(table["id"]))}')
      return None

    rows = []
    with open(table['log_file'], 'r') as f:
      for line in f:
        time_s, payload_s, protocol_s = line.split('\t')
        payload = json.loads(payload_s)
        protocol = json.loads(protocol_s)

        # Filter rows by persons
        person = protocol.get('uid')
        if select_persons is None or person in select_persons:

          # Use default column keys
          rows.append({
            **payload,
            TIME_KEY: datetime.datetime.strptime(time_s, '%Y-%m-%dT%H:%M:%S.%fZ'),
            GRADE_KEY: payload.get('points'),
            PERSON_KEY: person,
          })

    if len(rows) == 0:
      return None
    
    data = pandas.DataFrame(rows)

    # Filter extra columns
    rm_cols = []
    if not include_personal:
      rm_cols.extend([])
    if exclude_columns:
      rm_cols.extend(exclude_columns)
    return data.drop(columns=[c for c in data.columns if c in rm_cols]).reset_index(drop=True)

  def file_columns(self, table, rows):
    return []

  def fetch_file(self, table, row, col_name, include_personal):
    return None

  def fetch_meta_json(self, table, row, include_personal):
    return None

  def drop_for_export(self, table, rows, volatile_columns):
    return rows

  def fetch_delay(self):
    pass
