from .Config import EXPORT_DIR, EXPORT_INDEX_JSON
from .Filters import Filters
from .LlamaStats import LlamaStats
from .ProgSnap2 import ProgSnap2
from .operations import filter_by_person, ensure_column_types
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
    l = len(self.sources)
    for i, s in enumerate(index.get('sources', [])):
      tables = read_json((dir, s['index_file']))
      require(not tables is None, f'Unable to read {dir}/{s["index_file"]}')
      self.sources.append({ **s, 'id': l + i, 'dir': dir, 'tables': tables })
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

  def _persons(self, select):
    persons = set([])
    for s in [] if select is None else as_list(select):
      if 'persons' in s:
        persons.update(s['persons'])
    return persons if len(persons) > 0 else None

  def get(self, select=None):
    for s in self._select(select):
      for t in s['tables']:
        p_in = self._persons(t.get('inc_filters'))
        p_out = self._persons(t.get('exc_filters'))
        rows = filter_by_person(read_csv((s['dir'], t['data_file'])), p_in, p_out)
        ensure_column_types(rows)
        yield s, t, rows

  def progsnap2(self, select, export_dir, acos_initial_codes=None):
    exporter = ProgSnap2(self.get(select), export_dir, acos_initial_codes)
    exporter.process()
    exporter.write()

  def _cached_series(self, target, select):
    key = (select, target)
    try:
      return next(pl for k, pl in self.cache if k == key)
    except StopIteration:
      if target == 'overall':
        pl = LlamaStats.overall_series(self.get(select))
      elif target == 'learner':
        pl = LlamaStats.learner_series(self.get(select))
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
