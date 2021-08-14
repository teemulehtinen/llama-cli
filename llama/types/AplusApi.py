import requests
import time
import json

class AplusApi:

  API_URL = '{host}/api/v2/'
  COURSE_LIST = '{url}courses/'
  EXERCISE_LIST = '{url}courses/{course_id:d}/exercises/'
  SUBMISSION_CSV = '{url}courses/{course_id:d}/submissiondata/?exercise_id={exercise_id:d}&best=no&format=csv'
  SUBMISSION_DETAILS = '{url}submissions/{submission_id:d}'
  REQUEST_DELAY = 1 #sec

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
