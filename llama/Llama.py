from .types import get_sources_with_tables

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
      rows, _ = s['api'].fetch_rows(t, only_cache=True)
      if not rows is None:
        if files:
          if len(list(s['api'].file_columns(t, rows))) > 0:
            yield s, t, rows
        else:
          yield s, t, rows
  
  def name(self, source=None, table=None, files=False):
    for source, table, rows in self.get(source, table, files):
      yield {
        'source_id': source['id'],
        'table_id': table['id'],
        'table': table['name'],
        'rows_n': rows.shape[0],
      }

  def _sample(self, n, source, table):
    for s, t in self.select_tables(source, table):
      rows, _ = s['api'].fetch_rows(t, only_cache=True)
      yield s, t, None if rows is None else rows.sample(n)
  
  def sample(self, n=10, source=None, table=None):
    for _, _, sample in self._sample(n, source, table):
      if not sample is None:
        yield sample

  def sample_files(self, n=10, source=None, table=None):
    for s, t, sample in self._sample(n, source, table):
      if not sample is None:
        return [f for f in s['api'].fetch_files(t, sample, only_cache=True)]
