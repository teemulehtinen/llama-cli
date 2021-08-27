import time
from .AbstractDjangoApi import AbstractDjangoApi
from ..common import read_json, write_json

class AplusApi(AbstractDjangoApi):

  API_URL = '{host}/api/v2/'
  COURSE_LIST = '{url}courses/'
  EXERCISE_LIST = '{url}courses/{course_id:d}/exercises/'
  SUBMISSION_ROWS = '{url}courses/{course_id:d}/submissiondata/?exercise_id={exercise_id:d}&best=no&format=csv'
  SUBMISSION_DETAILS = '{url}submissions/{submission_id:d}'
  REQUEST_DELAY = 1 #sec

  EXERCISE_JSON = '{course_id}-exercise-list.json'
  SUBMISSION_CSV = '{course_id}-{exercise_id}-rows.csv'

  STATUS_KEY = 'Status'
  TIME_KEY = 'Time'
  GRADE_KEY = 'Grade'
  PENALTY_KEY = 'Penalty'
  PSEUDO_USER_KEY = 'UserID'
  PSEUDO_ITEM_KEY = 'SubmissionID'
  PERSONAL_KEYS = ['StudentID', 'Email']

  @classmethod
  def create(cls, host, token):
    url = cls.API_URL.format(host=f'{"" if "://" in host else "https://"}{host}')
    return AplusApi(url, token), url

  def __init__(self, url, token, course_id=None):
    super().__init__(token, self.REQUEST_DELAY)
    self.url = url
    self.course_id = course_id

  def list_courses(self):
    courses = self.get_paged_json(self.COURSE_LIST.format(url=self.url))
    courses.sort(key=lambda c: c['id'], reverse=True)
    return courses
  
  def list_tables(self, try_cache=True, only_cache=False):
    return self.cached_json_or_get(
      lambda: self.get_table_details(),
      self.EXERCISE_JSON.format(course_id=self.course_id),
      try_cache,
      only_cache
    )

  def get_table_details(self):
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
        time.sleep(self.REQUEST_DELAY)
        details = self.get_json(e['url'])
        form = (details.get('exercise_info') or {}).get('form_spec', [])
        entry['columns'] = [{ 'key': f['key'] } for f in form if f['type'] != 'static']
        tables.append(entry)
    return tables

  def fetch_rows(self, table, personal=False, only_cache=False):
    file_name = self.SUBMISSION_CSV.format(course_id=self.course_id, exercise_id=table['id'])
    rows, cached = self.cached_csv_or_get(
      lambda: self.get_filtered_rows(table, personal),
      file_name,
      True,
      only_cache
    )

    # A-plus does not offer filtering by e.g. time/id to extend previously fetched rows
    if cached and not rows is None:
      print(f'* Cached {table["name"]}: to update, remove {file_name}')
    return rows, cached

  def get_filtered_rows(self, table, personal):
    url = self.SUBMISSION_ROWS.format(url=self.url, course_id=self.course_id, exercise_id=table['id'])
    data = self.get_csv(url)
    
    # Reject rows where status NOT 'ready'
    if self.STATUS_KEY in data:
      data = data[data[self.STATUS_KEY] == 'ready']

    # Parse time
    if self.TIME_KEY in data:
      data[self.TIME_KEY] = self.col_to_datetime(data[self.TIME_KEY])

    # Cancel late penalties to keep grades comparable
    def cancel_apply(row):
      if row[self.PENALTY_KEY] > 0:
        row[self.GRADE_KEY] /= row[self.PENALTY_KEY]
      return row
    if self.PENALTY_KEY in data:
      data = data.apply(cancel_apply, 1)

    # Filter down to requested columns
    cols = [self.PSEUDO_USER_KEY, self.PSEUDO_ITEM_KEY, self.TIME_KEY, self.GRADE_KEY]
    if personal:
      cols.extend(self.PERSONAL_KEYS)
    cols.extend(c['key'] for c in table['columns'])
    data = data.drop(columns=[c for c in data.columns if not c in cols]).reset_index(drop=True)

    time.sleep(self.REQUEST_DELAY)
    return data

  @staticmethod
  def en_name(name):
    return ''.join(
      (p[3:] if p.startswith('en:') else p).replace('  ', ' ')
      for p in name.split('|')
      if len(p) < 3 or p[2] != ':' or p.startswith('en:')
    )
