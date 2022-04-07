import os
import re
import json
import pandas
from .AbstractApi import AbstractApi
from ..Config import TIME_KEY, GRADE_KEY, PERSON_KEY

class MongodumpApi(AbstractApi):

  @classmethod
  def create(cls, source_id, main_file, database_config):
    return MongodumpApi(source_id, main_file, database_config)

  def __init__(self, source_id, main_file, database_config):
    super().__init__(source_id)
    self.config = database_config
    self.dir = os.path.dirname(main_file)
    _, self.ext = os.path.splitext(main_file)
    self.main_file = main_file
    self.loaded_dump = None
    self.drop_columns_re = re.compile(self.config['drop_keys_re'])
    self.show_columns_re = re.compile(self.config['show_keys_re'])

  def fetch_tables_json(self):
    dump = self.parse_dump()
    modules = []
    
    def row_filter(row):
      for type, key, value in self.config['table_filters']:
        if (
          (type == '==' and row.get(key) == value)
          or (type == '!=' and row.get(key) != value)
        ):
          return True
      return False
    
    for row in dump:
      module_id = row.get(self.config['module_key'])
      table_id = row.get(self.config['table_key'])
      if module_id is None or table_id is None or row_filter(row):
        continue
      module = next((m for m in modules if m['id'] == module_id), None)
      if module is None:
        module = { 'id': module_id, 'tables': [] }
        modules.append(module)
      table = next((t for t in module['tables'] if t['full_id'] == table_id), None)
      if table is None:
        module['tables'].append({
          'module_id': module_id,
          'module_name': str(row.get(self.config['module_name_key'])),
          'id': table_id.split('/')[-1],
          'full_id': table_id,
          'name': str(row.get(self.config['table_name_key'])),
          'max_points': row.get(self.config['grade_max_key']),
          'max_submissions': None,
          'columns': [
            { 'key': k } for k in row.keys()
            if not self.drop_columns_re.match(k) and self.show_columns_re.match(k)
          ],
        })
    return [t for m in modules for t in m['tables']]

  def fetch_rows_csv(self, table, old_rows, include_personal, select_persons, exclude_columns):

    # NOTE: no use to extend previously fetched rows from complete database dump
    if not old_rows is None:
      print(f'* Cached {table["name"]}: to update, remove {os.path.join(*self.table_csv_name(table["id"]))}')
      return None

    data = pandas.DataFrame(self.parse_dump())
    
    # Filter rows to the target
    print('> Selecting for #{}'.format(table['id']))
    data = data[data[self.config['table_key']] == table['full_id']]
    for type, key, value in self.config['table_filters']:
      if key in data:
        if type == '==':
          data = data[data[key] != value]
        elif type == '!=':
          data = data[data[key] == value]
    data = data.dropna(axis=1, how='all')

    # Filter rows by persons
    if not select_persons is None:
      data = data[data[self.config['pseudo_user_key']].isin(select_persons)]

    # Use default column keys
    rm_cols = []
    for def_key, old_key in [
      (TIME_KEY, self.config['time_key']),
      (GRADE_KEY, self.config['grade_key']),
      (PERSON_KEY, self.config['pseudo_user_key']),
    ]:
      if def_key != old_key:
        data[def_key] = data[old_key]
        rm_cols.append(old_key)

    # Filter extra columns
    rm_cols.extend(c for c in data.columns if self.drop_columns_re.match(c))
    if not include_personal:
      rm_cols.extend(self.config['personal_keys'])
    if exclude_columns:
      rm_cols.extend(exclude_columns)
    return data.drop(columns=[c for c in data.columns if c in rm_cols]).reset_index(drop=True)

  def file_columns(self, table, rows):
    return [c for c in rows.columns if c.startswith('files_') and c.endswith('_key')]

  def fetch_file(self, table, row, col_name, include_personal):
    return row.get(col_name.replace('_key', '_content'))

  def fetch_meta_json(self, table, row, include_personal):
    return None

  def drop_for_export(self, table, rows, volatile_columns):
    rm_cols = [self.config['pseudo_item_key']] + self.config['personal_keys']
    return rows.drop(columns=[c for c in rows.columns if c in rm_cols])

  def fetch_delay(self):
    pass

  def parse_dump(self):
    if self.loaded_dump is None:
      cached_links = {}
      self.loaded_dump = self.parse_dump_file(self.main_file, cached_links)
    return self.loaded_dump

  def parse_dump_file(self, file_path, cached_links):

    def load_linked_file(key):
      for name in [p.format(key) for p in self.config['references_to_collections']]:
        path = os.path.join(self.dir, name + self.ext)
        if os.path.exists(path):
          return self.parse_dump_file(path, cached_links)
      return None

    def find_linked_file(key):
      if not key in cached_links:
        cached_links[key] = load_linked_file(key)
      return cached_links[key]

    def find_linked_item(key, id):
      for item in find_linked_file(key) or []:
        if item['_id'] == id:
          return item
      return { '_id': id }

    def unpack_val(out, key, val):
      if isinstance(val, list):
        # Support selected list types (custom key-value map, references)
        if len(val) > 0:
          if isinstance(val[0], dict):
            local_keys = set(val[0].keys())
            if local_keys == {'_id', 'key', 'value'}:
              for e in val:
                out['_'.join([key, e.get('key')])] = e.get('value')
            elif local_keys == {'$oid'}:
              for i, e in enumerate(val):
                for k, v in find_linked_item(key, e.get('$oid')).items():
                  unpack_val(out, '_'.join([key, str(i), k]), v)
      elif isinstance(val, dict):
        # Support selected special types (date, binary, reference)
        local_keys = set(val.keys())
        if key == '_id':
          out[key] = val.get('$oid')
        elif local_keys == {'$date'}:
          out[key] = val.get('$date')
        elif local_keys == {'$binary', '$type'}:
          out[key] = val.get('$binary')
        elif local_keys == {'$oid'}:
          for k, v in find_linked_item(key, val['$oid']).items():
            unpack_val(out, '_'.join([key, k]), v)
      else:
        out[key] = val

    print('> Parsing database dump {}'.format(file_path))
    loaded = []
    with open(file_path, 'r') as file:
      for line in file:
        row = json.loads(line)
        out = {}
        for key, val in row.items():
          if key != '__v':
            unpack_val(out, key, val)
        loaded.append(out)
    return loaded
