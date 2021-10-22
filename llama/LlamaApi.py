from .Config import EXPORT_DIR, EXPORT_INDEX_JSON, TIME_KEY
from .LlamaStats import LlamaStats
from .operations import parse_timecolumn
from .common import require, as_list, read_json, read_csv

class LlamaApi:

  def __init__(self, *directories):
    self.sources = []
    self.persons = []
    if len(directories) == 0:
      self._read_dir(EXPORT_DIR)
    else:
      for d in directories:
        self._read_dir(d)
  
  def _read_dir(self, dir):
    index = read_json((dir, EXPORT_INDEX_JSON))
    require(index, f'Unable to read ${dir}/${EXPORT_INDEX_JSON}')
    self.sources.extend({ **s, 'dir': dir } for s in index.get('sources', []))
    p = index.get('persons')
    if p:
      self.persons.append(p)

  @staticmethod
  def _match_table(table, checks):
    for c in checks:
      if c.startswith('#') and c[1:] == table['id']:
        return True
      if c in table['name']:
        return True
    return False

  def _select(self, select=None):
    sources = []
    sc = select.get('source') if select else None
    tc = select.get('table') if select else None
    for i, s in enumerate(self.sources):
      s['i'] = i
      if sc is None or i in [int(c) for c in as_list(sc)]:
        if not 'tables' in s:
          s['tables'] = read_json((s['dir'], s['index_file']))
        tables = []
        for t in s['tables']:
          if tc is None or self._match_table(t, as_list(tc)):
            tables.append(t)
        sources.append({ **s, 'tables': tables })
    return sources
  
  def list(self, select=None):
    for s in self._select(select):
      print(f'Source {s["i"]}: {s["name"]}')
      for t in s['tables']:
        cols = [c['key'] for c in t['columns']]
        print(f'#{t["id"]} "{t["name"]}": {" ".join(cols)}')

  def get(self, select=None):
    for s in self._select(select):
      for t in s['tables']:
        rows = read_csv((s['dir'], t['data_file']))
        parse_timecolumn(rows)
        yield s, t, rows

  def exercise_description(self, select=None):
    for _, t, rows in self.get(select):
      descs = LlamaStats.exercise_description(LlamaStats.exercise_series(rows))
      print(t['name'])
      print(descs)

  def exercise_pdf(self, pdf_name=None, select=None):
    for _, t, rows in self.get(select):
      series = LlamaStats.exercise_series(rows)
      LlamaStats.exercise_plot(t['name'], series)
