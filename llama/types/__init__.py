from . import aplus

TYPES = [
  {
    'id': 'aplus',
    'name': 'A-plus-LMS, https://apluslms.github.io/',
    'add': aplus.interactive_connect,
  }
]

def select_type(id):
  for t in TYPES:
    if t['id'] == id:
      return t
  return None
