import os.path
import json
import uuid

CONFIG_FILE = '.llama'
TOKENS_FILE = '.tokens'

class Config:

  def __init__(self, version):
    self.data = {
      'llama': version,
      'sources': [],
      'privacy': 'pseudo',
      'consent': None,
    }
    self.exists = os.path.isfile(CONFIG_FILE)
    if self.exists:
      self.load()

  def load(self):
    self.data = self.join_tokens(
      self.read_json(CONFIG_FILE),
      self.read_json(TOKENS_FILE)
    )

  def write(self):
    data, tokens = self.split_tokens(self.data)
    self.write_json(CONFIG_FILE, data)
    if tokens:
      self.write_json(TOKENS_FILE, tokens)
      self.write_gitignore()
    self.exists = True

  @property
  def version(self):
    return self.data['llama']

  @property
  def sources(self):
    return self.data['sources']
  
  def set_sources(self, sources):
    self.data['sources'] = sources
    self.write()

  @property
  def privacy(self):
    return self.data['privacy']

  def set_privacy(self, privacy):
    self.data['privacy'] = privacy
    self.write()

  @property
  def consent(self):
    return self.data['consent']
  
  def set_consent(self, consent):
    self.data['consent'] = consent
    self.write()

  @staticmethod
  def read_json(file_name):
    if not os.path.isfile(file_name):
      return {}
    with open(file_name) as f:
      return json.loads(f.read())

  @staticmethod
  def write_json(file_name, data):
    with open(file_name, 'w') as f:
      f.write(json.dumps(data, indent=2))

  @staticmethod
  def write_gitignore():
    ignore_line = f'{TOKENS_FILE}\n'
    if not os.path.isfile('.gitignore'):
      with open('.gitignore', 'w') as f:
        f.write(ignore_line)
    else:
      with open('.gitignore', 'r+') as f:
        for line in f:
          if line == ignore_line:
            return
        f.write(ignore_line)

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
