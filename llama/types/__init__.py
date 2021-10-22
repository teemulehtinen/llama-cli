from ..common import require
from . import aplus

TYPES = [
  {
    'id': 'aplus',
    'name': 'A-plus-LMS, https://apluslms.github.io/',
    'add': aplus.interactive_connect,
    'construct': aplus.construct_client,
  }
]

def interactive_add(type):
  return type['add']()

def select_type(type):
  for t in TYPES:
    if t['id'] == type:
      return t
  return None

def create_client(src):
  t = select_type(src['type'])
  if t:
    return t['construct'](src)
  return None

def enumerate_sources(config):
  return [(i, src, create_client(src)) for i, src in enumerate(config.sources)]

def get_sources_with_tables(config):
  sources = []
  for i, src, api in enumerate_sources(config):
    tables, cached = api.list_tables(only_cache=True)
    require(cached, 'No table list loaded, use "list" command first')
    sources.append({
      'id': i,
      'name': src['name'],
      'type': src['type'],
      'index': api.table_list_json_name(),
      'tables': tables,
      'api': api,
    })
  return sources
