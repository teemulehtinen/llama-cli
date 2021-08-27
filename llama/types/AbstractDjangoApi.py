import time
from .AbstractApi import AbstractApi
from ..common import read_json, write_json

class AbstractDjangoApi(AbstractApi):

  def __init__(self, token, req_delay):
    self.token = token
    self.req_delay = req_delay

  def get(self, url):
    return super().get(url, headers={'Authorization': f'Token {self.token}'})

  def get_paged_json(self, url):
    results = []
    next = url
    while next:
      response = self.get_json(next)
      results.extend(response['results'])
      next = response['next']
      if next:
        time.sleep(self.req_delay)
    return results
