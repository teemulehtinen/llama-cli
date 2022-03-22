import os
import json
import pandas
from .AbstractApi import AbstractApi
from ..Config import PERSON_KEY, GRADE_KEY

class MongodumpApi(AbstractApi):

  @classmethod
  def create(cls, source_id, main_file):
    return MongodumpApi(source_id, main_file)

  def __init__(self, source_id, main_file):
    super().__init__(source_id)
    _, ext = os.path.splitext(main_file)
    self.dir = os.path.dirname(main_file)
    self.ext = ext
    self.main_file = main_file

  def fetch_tables_json(self):
    dump = self.parse_json_dump(self.main_file)
    print(pandas.DataFrame(dump).columns)
    os._exit(1)
    tables = []
    modules = self.get_paged_json(self.EXERCISE_LIST.format(url=self.url, course_id=self.course_id))
    for m in modules:
      for e in m['exercises']:
        entry = {
          'module_id': m['id'],
          'module_name': self.en_name(m['display_name']),
          'id': e['id'],
          'name': self.en_name(e['display_name']),
          'max_points': e['max_points'],
          'max_submissions': e['max_submissions'],
        }
        self.fetch_delay()
        details = self.fetch_json(e['url'])
        form = (details.get('exercise_info') or {}).get('form_spec', [])
        entry['columns'] = [{ 'key': f['key'] } for f in form if f['type'] != 'static']
        tables.append(entry)
    return tables

  def fetch_rows_csv(self, table, old_rows, include_personal, select_persons, exclude_columns):

    # NOTE: A-plus does not offer filtering by time or id to extend previously fetched rows
    if not old_rows is None:
      print(f'* Cached {table["name"]}: to update, remove {self.table_csv_name(table["id"])}')
      return None

    url = self.SUBMISSION_ROWS.format(url=self.url, course_id=self.course_id, exercise_id=table['id'])
    data = self.fetch_csv(url)
    
    # Reject rows where status NOT 'ready'
    if self.STATUS_KEY in data:
      data = data[data[self.STATUS_KEY] == 'ready']

    # Filter rows by persons
    if not select_persons is None:
      data = data[data[self.PSEUDO_USER_KEY].isin(select_persons)]

    # Cancel late penalties to keep all grades comparable
    def cancel_apply(row):
      if row[self.PENALTY_KEY] > 0:
        row[GRADE_KEY] /= row[self.PENALTY_KEY]
      return row
    if self.PENALTY_KEY in data:
      data = data.apply(cancel_apply, 1)

    # Use default column keys:
    # TIME_KEY matches
    # GRADE_KEY matches
    data[PERSON_KEY] = data[self.PSEUDO_USER_KEY]

    # Filter extra columns
    rm_cols = self.REMOVE_KEYS
    if not include_personal:
      rm_cols.extend(self.REMOVE_PERSONAL_KEYS)
    if exclude_columns:
      rm_cols.extend(exclude_columns)
    return data.drop(columns=[c for c in data.columns if c in rm_cols]).reset_index(drop=True)

  def file_columns(self, table, rows):
    return [c for c in rows.columns if self.file_key_re.match(c)]
  
  def fetch_file(self, table, row, col_name, include_personal):
    url_match = self.file_val_re.match(row[col_name])
    if url_match:
      content = self.fetch(url_match.group(0)).text
      if not include_personal:
        content = self.personal_re.sub('', content)
      return content
    return None

  def fetch_meta_json(self, table, row, include_personal):
    url = self.SUBMISSION_DETAILS.format(url=self.url, submission_id=row[self.PSEUDO_ITEM_KEY])
    data = self.fetch_json(url)
    return { k: data.get(k) for k in self.META_KEYS }

  def drop_for_export(self, table, rows, volatile_columns):
    pere = self.personal_re
    for name in volatile_columns or []:
      if name in rows.columns:
        rows[name] = rows[name].apply(lambda s: pere.sub('', str(s)) if s else s)
    return rows.drop(columns=[c for c in rows.columns if c in self.REMOVE_AT_EXPORT])

  def parse_json_dump(self, file_path):
    cached_links = {}

    def load_linked_file(key):
      # Try to guess collection names from a reference field name
      for name in [key, key + 's', 'submitted' + key]:
        path = os.path.join(self.dir, name + self.ext)
        if os.path.exists(path):
          return self.parse_json_dump(path)
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

    rows_out = []
    with open(file_path, 'r') as file:
      for line in file:
        row = json.loads(line)
        out = {}
        for key, val in row.items():
          if key != '__v':
            unpack_val(out, key, val)
        rows_out.append(out)
    return rows_out
