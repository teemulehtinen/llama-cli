from llama.types.AbstractApi import AbstractApi
import requests
import time
import json
from ..common import write_json, read_json

def en_name(name):
  return ''.join(
    (p[3:] if p.startswith('en:') else p).replace('  ', ' ')
    for p in name.split('|')
    if len(p) < 3 or p[2] != ':' or p.startswith('en:')
  )

class AplusApi(AbstractApi):

  API_URL = '{host}/api/v2/'
  COURSE_LIST = '{url}courses/'
  EXERCISE_LIST = '{url}courses/{course_id:d}/exercises/'
  SUBMISSION_CSV = '{url}courses/{course_id:d}/submissiondata/?exercise_id={exercise_id:d}&best=no&format=csv'
  SUBMISSION_DETAILS = '{url}submissions/{submission_id:d}'
  REQUEST_DELAY = 1 #sec
  EXERCISE_JSON = '{course_id}-exercise-list.json'

  @classmethod
  def create(cls, host, token):
    url = cls.API_URL.format(host=f'{"" if "://" in host else "https://"}{host}')
    return AplusApi(url, token), url

  def __init__(self, url, token, course_id=None):
    self.url = url
    self.token = token
    self.course_id = course_id

  def list_courses(self):
    courses = self.get_paged_json(self.COURSE_LIST.format(url=self.url))
    courses.sort(key=lambda c: c['id'], reverse=True)
    return courses
  
  def list_tables(self, try_cache=True, only_cache=False):
    file_name = self.EXERCISE_JSON.format(course_id=self.course_id)
    if try_cache or only_cache:
      exercises = read_json(file_name)
      if exercises:
        return exercises, True
      elif only_cache:
        return None, False
    exercises = []
    modules = self.get_paged_json(self.EXERCISE_LIST.format(url=self.url, course_id=self.course_id))
    for m in modules:
      for e in m['exercises']:
        entry = {
          'module_id': m['id'],
          'module_name': en_name(m['display_name']),
          'id': e['id'],
          'name': en_name(e['display_name']),
          'max_points': e['max_points'],
          'max_submissions': e['max_submissions'],
        }
        time.sleep(self.REQUEST_DELAY)
        details = self.get_json(e['url'])
        form = (details.get('exercise_info') or {}).get('form_spec', [])
        entry['columns'] = [{ 'key': f['key'] } for f in form if f['type'] != 'static']
        exercises.append(entry)
    write_json(file_name, exercises)
    return exercises, False

  def fetch(self):
    pass

  def fetch_related(self):
    pass

  def get(self, url):
    print('> aplus GET', url)
    return requests.get(url, headers={'Authorization': f'Token {self.token}'})

  def get_json(self, url):
    return json.loads(self.get(url).text)

  def get_paged_json(self, url):
    results = []
    next = url
    while next:
      response = self.get_json(next)
      results.extend(response['results'])
      next = response['next']
      if next:
        time.sleep(self.REQUEST_DELAY)
    return results
