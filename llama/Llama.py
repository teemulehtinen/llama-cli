from .types import get_sources_with_tables
from .common import count

class Llama:

  def __init__(self, config):
    self.config = config
    self.sources = None

  def get_sources(self):
    if self.sources is None:
      self.sources = get_sources_with_tables(self.config)
    return self.sources

  def select_tables(self, source=None, table=None):
    def match(t):
      if table.startswith('#'):
        return table[1:] == str(t['id'])
      return table in t['name']
    for s in self.get_sources():
      if source is None or source == s['id']:
        for t in s['tables']:
          if table is None or match(t):
            yield s, t
  
  def get(self, source=None, table=None, files=False):
    for s, t in self.select_tables(source, table):
      rows = s['api'].get_export_rows(t)
      if not rows is None:
        if files:
          if count(s['api'].file_columns(t, rows)) > 0:
            yield s, t, rows
        else:
          yield s, t, rows
  
  def name(self, source=None, table=None, files=False):
    for s, t, rows in self.get(source, table, files):
      yield {
        'source_id': s['id'],
        'table_id': t['id'],
        'table': t['name'],
        'rows_n': rows.shape[0],
      }
  
  def get_files(self, source=None, table=None):
    for s, t, rows in self.get(source, table, True):
      for r in s['api'].get_export_files(t, rows):
        yield { 'source': s['id'], 'table': t, **r }
  
  def get_meta(self, source=None, table=None, files=False):
    for s, t, rows in self.get(source, table, files):
      for r in s['api'].get_export_meta(t, rows):
        yield { 'source': s['id'], 'table': t, **r }

  def sample(self, n=10, source=None, table=None, files=False):
    for s, t, rows in self.get(source, table, files):
      yield s, t, None if rows is None else rows.sample(n)

  def sample_files(self, n=10, source=None, table=None):
    for s, t, sample in self.sample(n, source, table, True):
      for r in s['api'].get_export_files(t, sample):
        yield { 'source': s['id'], 'table': t, **r }

  def sample_meta(self, n=10, source=None, table=None, files=False):
    for s, t, sample in self.sample(n, source, table, files):
      for r in s['api'].get_export_meta(t, sample):
        yield { 'source': s['id'], 'table': t, **r }
