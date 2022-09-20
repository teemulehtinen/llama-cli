import os.path
import uuid
from .common import read_json, write_json

VERSION = '1.0.13'
CONFIG_FILE = '.llama'
TOKENS_FILE = '.tokens'
STORAGE_DIR = 'fetched'
EXPORT_DIR = 'export'
EXPORT_INDEX_JSON = 'index.json'

# These keys should be in the data tables (if appropriate)
TIME_KEY = 'Time'
PERSON_KEY = 'Person'
GRADE_KEY = 'Grade'

class Config:

  def __init__(self):
    self.data = {
      'llama': VERSION,
      'sources': [],
      'privacy': 'pseudo',
      'exclude': [],
    }
    self.exists = os.path.isfile(CONFIG_FILE)
    if self.exists:
      self.load()

  def load(self):
    self.data = self.join_tokens(read_json(CONFIG_FILE) or {}, read_json(TOKENS_FILE) or {})
    
    # Backwards compatibility
    for src in self.data['sources']:
      if not 'type' in src and 'id' in src:
        src['type'] = src['id']
        del src['id']

  def write(self):
    data, tokens = self.split_tokens(self.data)
    write_json(CONFIG_FILE, data)
    if tokens:
      write_json(TOKENS_FILE, tokens)
    self.write_gitignore()
    self.exists = True

  @property
  def version(self):
    return self.data.get('llama')

  @property
  def sources(self):
    return self.data.get('sources', [])
  
  def set_sources(self, sources):
    self.data['sources'] = list(sources)
    self.write()

  @property
  def privacy(self):
    return self.data.get('privacy', 'pseudo')

  def set_privacy(self, privacy):
    self.data['privacy'] = privacy
    self.write()

  @property
  def exclude(self):
    return self.data.get('exclude', [])
  
  def set_exclude(self, exclude):
    self.data['exclude'] = list(exclude)
    self.write()

  @staticmethod
  def write_gitignore():
    ignore_lines = [f'{TOKENS_FILE}\n', f'{STORAGE_DIR}/\n']
    if not os.path.isfile('.gitignore'):
      with open('.gitignore', 'w') as f:
        for l in ignore_lines:
          f.write(l)
    else:
      with open('.gitignore', 'r+') as f:
        for line in f:
          if line in ignore_lines:
            ignore_lines.remove(line)
        for l in ignore_lines:
          f.write(l)

  @staticmethod
  def split_tokens(data):
    tokens = {}
    sources = []
    for s_in in data['sources']:
      if 'token' in s_in:
        s_out = { **s_in, 'token': str(uuid.uuid4()) }
        tokens[s_out['token']] = s_in['token']
        sources.append(s_out)
      else:
        sources.append(s_in)
    return { **data, 'sources': sources }, tokens

  @staticmethod
  def join_tokens(data, tokens):
    sources = []
    for s_in in data['sources']:
      if 'token' in s_in:
        if not s_in['token'] in tokens:
          print('Error: missing token for {}'.format(s_in['url']))
        sources.append({ **s_in, 'token': tokens.get(s_in['token'], '') })
      else:
        sources.append(s_in)
    return { **data, 'sources': sources }
