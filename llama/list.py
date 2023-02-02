from .types import enumerate_sources
from .operations import last_time
from .common import count
from .Filters import Filters

def format_source(i, name):
  return f'{i:d}: {name}'

def format_table(id, name, columns):
  return f'#{id} "{name}".[{",".join(c["key"] for c in columns)}]'

def print_sources(sources):
  for s in sources:
    print(format_source(s['id'], s['name']))
    for t in s['tables']:
      print(format_table(t['id'], t['name'], t['columns']))

def command(args, config):
  if args != [] and args != ['update']:
    print('Lists and updates available data tables and their fields\n')
    print('usage: llama list [update]\n')
  else:
    for i, src, api in enumerate_sources(config):
      print(format_source(i, src['name']))
      tables, cached = api.list_tables(args != ['update'])
      if cached:
        print('* Using cached tables, use "list update" to refetch')
      for t in tables:
        print(format_table(t['id'], t['name'], t['columns']), end=' ')
        rows, _ = api.fetch_rows(t, only_cache=True)
        rows_n = 0 if rows is None else rows.shape[0]
        if not rows is None and count(api.file_columns(t, rows)) > 0:
          file_n = count(api.fetch_files(t, rows, only_cache=True))
          print(f'{rows_n} rows, {file_n} files, last {last_time(rows)}')
        elif rows_n > 0:
          print(f'{rows_n} rows, last {last_time(rows)}')
        else:
          print('0 rows fetched')
