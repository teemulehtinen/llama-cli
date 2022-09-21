import os
import re
from ..Config import PERSON_KEY, GRADE_KEY
from .AbstractDjangoApi import AbstractDjangoApi

class AplusApi(AbstractDjangoApi):

  API_URL = '{host}/api/v2/'
  COURSE_LIST = '{url}courses/'
  EXERCISE_LIST = '{url}courses/{course_id:d}/exercises/'
  SUBMISSION_ROWS = '{url}courses/{course_id:d}/submissiondata/?exercise_id={exercise_id:d}&best=no&format=csv'
  SUBMISSION_DETAILS = '{url}submissions/{submission_id:d}'

  STATUS_KEY = 'Status'
  PENALTY_KEY = 'Penalty'
  PSEUDO_USER_KEY = 'UserID'
  PSEUDO_ITEM_KEY = 'SubmissionID'
  REMOVE_KEYS = [PSEUDO_USER_KEY, STATUS_KEY, 'ExerciseID', 'Category', 'Exercise', 'Graded', 'GraderEmail', 'Notified', 'NSeen', '_aplus_group', '__grader_lang']
  REMOVE_PERSONAL_KEYS = ['StudentID', 'Email']
  REMOVE_AT_EXPORT = [PSEUDO_ITEM_KEY] + REMOVE_PERSONAL_KEYS
  META_KEYS = ['exercise', 'submission_time', 'grading_time', 'grade', 'late_penalty_applied', 'feedback', 'grading_data']
  FILE_KEY_REGEXP = r'^file\d+$'
  FILE_VAL_REGEXP = r'^https:\/\/[^?]+'
  PERSONAL_REGEXP = r'^# (Nimi|Opiskelijanumero): .*$'

  @classmethod
  def create(cls, host, token):
    url = cls.API_URL.format(host=f'{"" if "://" in host else "https://"}{host}')
    return AplusApi(url, token), url

  def __init__(self, url, token, course_id=None):
    super().__init__(course_id, token)
    self.url = url
    self.course_id = course_id
    self.file_key_re = re.compile(self.FILE_KEY_REGEXP)
    self.file_val_re = re.compile(self.FILE_VAL_REGEXP)
    self.personal_re = re.compile(self.PERSONAL_REGEXP, flags=re.I | re.M)

  def list_courses(self):
    courses = self.get_paged_json(self.COURSE_LIST.format(url=self.url))
    courses.sort(key=lambda c: c['id'], reverse=True)
    return courses  

  def fetch_tables_json(self):
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
          'difficulty': e.get('difficulty'),
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
      print(f'* Cached {table["name"]}: to update, remove {os.path.join(*self.table_csv_name(table["id"]))}')
      return None

    url = self.SUBMISSION_ROWS.format(url=self.url, course_id=self.course_id, exercise_id=table['id'])
    data = self.fetch_csv(url)
    
    # Reject rows where status NOT 'ready'
    if self.STATUS_KEY in data:
      data = data[data[self.STATUS_KEY] == 'ready']

    # Filter rows by persons
    if not select_persons is None:
      data = data[data[self.PSEUDO_USER_KEY].astype(str).isin(select_persons)]

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

  @staticmethod
  def en_name(name):
    return ''.join(
      (p[3:] if p.startswith('en:') else p).replace('  ', ' ')
      for p in name.split('|')
      if len(p) < 3 or p[2] != ':' or p.startswith('en:')
    )
