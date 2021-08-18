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

def select_type(id):
  for t in TYPES:
    if t['id'] == id:
      return t
  return None

def create_client(src):
  t = select_type(src["id"])
  if t:
    return t['construct'](src)
  return None

def enumerate_sources(config):
  return [(i, src, create_client(src)) for i, src in enumerate(config.sources)]
