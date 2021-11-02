from .Config import EXPORT_DIR, EXPORT_INDEX_JSON
from .Filters import Filters
from .LlamaStats import LlamaStats
from .operations import parse_timecolumn
from .plotting import multipage_plot_or_show
from .common import (
  require, as_list, read_json, read_csv,
  write_or_print, df_from_iterator
)

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
    require(not index is None, f'Unable to read {dir}/{EXPORT_INDEX_JSON}')
    for i, s in enumerate(index.get('sources', [])):
      tables = read_json((dir, s['index_file']))
      require(not tables is None, f'Unable to read {dir}/{s["index_file"]}')
      self.sources.append({ **s, 'id': i, 'dir': dir, 'tables': tables })
    p = index.get('persons')
    if p:
      self.persons.append(p)

  def _select(self, select=None):
    return Filters([] if select is None else as_list(select), True).filter(self.sources)

  def list(self, select=None):
    for s in self._select(select):
      print(f'Source {s["id"]}: {s["name"]}')
      for t in s['tables']:
        cols = [c['key'] for c in t['columns']]
        print(f'#{t["id"]} "{t["name"]}": {" ".join(cols)}')

  def get(self, select=None):
    for s in self._select(select):
      for t in s['tables']:
        rows = read_csv((s['dir'], t['data_file']))
        parse_timecolumn(rows)
        yield s, t, rows

  def overall_description(self, select=None):
    series = LlamaStats.overall_series(self.get(select))
    print(f'Table count: {series["_tables"]}')
    print(LlamaStats.description(series))
    print(series['_week'], series['_weekday'], series['_24hour'])

  def overall_pdf(self, select=None, pdf_name=None):
    multipage_plot_or_show(
      pdf_name,
      [LlamaStats.overall_series(self.get(select))],
      lambda r: LlamaStats.overall_plot(r)
    )

  def learner_description(self, persons=None, select=None):
    for series in LlamaStats.learner_series(self.get(select), persons):
      print(f'Person: {series["_person"]}')
      print(LlamaStats.description(series))
      print(series['_week'], series['_weekday'], series['_24hour'])

  def learner_pdf(self, persons=None, select=None, pdf_name=None):
    multipage_plot_or_show(
      pdf_name,
      LlamaStats.learner_series(self.get(select), persons),
      lambda r: LlamaStats.learner_plot(r)
    )
  
  def learner_variables(self, persons=None, select=None, csv_name=None):
    write_or_print(df_from_iterator(
      LlamaStats.learner_variables(ls)
      for ls in LlamaStats.learner_series(self.get(select), persons)
    ), csv_name)

  def exercise_description(self, select=None):
    for _, t, rows in self.get(select):
      series = LlamaStats.exercise_series(rows)
      print(t['name'])
      print(LlamaStats.description(series))

  def exercise_pdf(self, select=None, pdf_name=None):
    multipage_plot_or_show(
      pdf_name,
      self.get(select),
      lambda r: LlamaStats.exercise_plot(r[1], LlamaStats.exercise_series(r[2]))
    )

  def exercise_variables(self, select=None, csv_name=None):
    write_or_print(df_from_iterator(
      LlamaStats.exercise_variables(table, LlamaStats.exercise_series(rows))
      for _, table, rows in self.get(select)
    ), csv_name)
