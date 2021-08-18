from .AplusApi import AplusApi
from ..common import require, input_selection

def interactive_connect():
  print('This will add an A-plus-LMS course as a source for learning data.')
  print('API token will be stored in separate file that is ignored for git.')
  host = input('Enter host name, e.g. plus.domain.org: ')
  token = input('Enter token from your A-plus profile page: ')
  require(host and token)
  api, url = AplusApi.create(host, token)
  courses = api.list_courses()
  print('Available courses')
  i = input_selection('{code} {name} - {instance_name}'.format(**c) for c in courses)
  require(not i is None)
  course = courses[i]
  return {
    'id': 'aplus',
    'url': url,
    'token': token,
    'course_id': course['id'],
    'name': course['html_url'],
  }

def construct_client(src):
  return AplusApi(src['url'], src['token'], src['course_id'])
