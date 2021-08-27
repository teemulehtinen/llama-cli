class Filters:

  # TODO fix matching children/parents

  def __init__(self, reverse=True):
    self.reverse = reverse
    self.row_filters = []
    self.col_filters = []

  def add(self, filters):
    for f in filters:
      if not f['value'] is None:
        self.row_filters.append(f)
      else:
        self.col_filters.append(f)
    return self
 
  def filter_columns(self, sources):
    matches = [self.match(f, sources) for f in self.col_filters]
    out = []
    for i, s in enumerate(sources):
      source_matches = [m[i] for m in matches]
      out_tables = []
      for j, t in enumerate(s['tables']):
        table_matches = [m['tables'][j] for m in source_matches]
        out_columns = []
        for k, c in enumerate(t['columns']):
          column_matches = [m['columns'][k] for m in table_matches]
          if all(m.get('match', False) for m in column_matches):
            out_columns.append(c)
        if all(m.get('match', False) for m in table_matches):
          out_tables.append(t)
      if all(m.get('match', False) for m in source_matches):
        out.append(s)
    return out

  def filter_rows(self, rows):
    print('TODO')

  def match(self, filter, sources):
    match = [self._match_source(filter, s) for s in sources]
    if not filter['reverse'] if self.reverse else filter['reverse']:
      return self._reverse_match(match)
    return match

  @classmethod
  def _match_source(cls, filter, source):
    if (
      filter['source'] is None
      or filter['source'] == source['id']
    ):
      return {
        **source,
        'tables': [cls._match_table(filter, t) for t in source['tables']],
        'match': not filter['source'] is None,
      }
    return source
 
  @classmethod
  def _match_table(cls, filter, table):
    if (
      filter['table'] is None
      or (filter['table_by_id'] and filter['table'] == str(table['id']))
      or (not filter['table_by_id'] and filter['table'] in table['name'])
    ):
      return {
        **table,
        'columns': [cls._match_column(filter, c) for c in table['columns']],
        'match': not filter['table'] is None,
      }
    return table

  @staticmethod
  def _match_column(filter, column):
    if (
      not filter['column'] is None
      and filter['column'] in column['name']
    ):
      return {
        **column,
        'match': True,
      }
    return column

  @staticmethod
  def _reverse_match(sources):
    return [{
      **s,
      'match': not s.get('match', False),
      'tables': [{
        **t,
        'match': not t.get('match', False),
        'columns': [{
          **c,
          'match': not c.get('match', False)
        } for c in t['columns']],
      } for t in s['tables']],
    } for s in sources]
