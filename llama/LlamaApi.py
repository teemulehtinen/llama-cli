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
    self.cache = []
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

  def _cached_series(self, target, select):
    key = {
      **{
        k: v for k, v in (select or {}).items()
        if (target == 'learner' or k != 'persons')
      },
      'target': target
    }
    try:
      return next(pl for k, pl in self.cache if k == key)
    except StopIteration:
      if target == 'overall':
        pl = LlamaStats.overall_series(self.get(select))
      elif target == 'learner':
        pl = LlamaStats.learner_series(self.get(select), (select or {}).get('persons'))
      elif target == 'exercise':
        pl = [LlamaStats.exercise_series(t, rows) for _, t, rows in self.get(select)]
      else:
        return None
      self.cache.append((key, pl))
      return pl
  
  def _print_description(self, series):
    print(series['_values'])
    print(LlamaStats.description(series).transpose())

  def overall_description(self, select=None):
    ovseries = self._cached_series('overall', select)
    self._print_description(ovseries)

  def overall_pdf(self, select=None, pdf_name=None):
    multipage_plot_or_show(
      pdf_name,
      [self._cached_series('overall', select)],
      lambda ovseries: LlamaStats.overall_plot(ovseries)
    )

  def learner_description(self, select=None):
    for leseries in self._cached_series('learner', select):
      self._print_description(leseries)

  def learner_pdf(self, select=None, pdf_name=None):
    ovseries = self._cached_series('overall', select)
    multipage_plot_or_show(
      pdf_name,
      self._cached_series('learner', select),
      lambda leseries: LlamaStats.learner_plot(leseries, ovseries)
    )
  
  def learner_variables(self, select=None, csv_name=None):
    write_or_print(df_from_iterator(
      LlamaStats.learner_variables(leseries)
      for leseries in self._cached_series('learner', select)
    ), csv_name)

  def exercise_description(self, select=None):
    for exseries in self._cached_series('exercise', select):
      self._print_description(exseries)

  def exercise_pdf(self, select=None, pdf_name=None):
    ovseries = self._cached_series('overall', select)
    multipage_plot_or_show(
      pdf_name,
      self._cached_series('exercise', select),
      lambda exseries: LlamaStats.exercise_plot(exseries, ovseries)
    )

  def exercise_variables(self, select=None, csv_name=None):
    write_or_print(df_from_iterator(
      LlamaStats.exercise_variables(exseries)
      for exseries in self._cached_series('exercise', select)
    ), csv_name)
