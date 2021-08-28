from .AbstractApi import AbstractApi
from ..common import read_json, write_json

class AbstractDjangoApi(AbstractApi):

  def __init__(self, source_id, token):
    super().__init__(source_id)
    self.token = token

  def fetch(self, url, headers={}):
    headers['Authorization'] = f'Token {self.token}'
    return super().fetch(url, headers=headers)

  def get_paged_json(self, url):
    results = []
    next = url
    while next:
      response = self.fetch_json(next)
      results.extend(response['results'])
      next = response['next']
      if next:
        self.fetch_delay()
    return results
