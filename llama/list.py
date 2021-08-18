from .types import enumerate_sources

def format_source(i, name):
  return f'{i:d}: {name}'

def format_table(id, name, columns):
  return f'#{id} "{name}".[{",".join(columns)}]'

def command(args, config):
  if args != [] and args != ['update']:
    print('Lists and updates available data tables and their fields\n')
    print('usage: llama list [update]\n')
  for i, src, api in enumerate_sources(config.sources):
    print(format_source(i, src['name']))
    tables, cached = api.list_tables(args != ['update'])
    if cached:
      print('* Using cached tables, use "list update" to refetch')
    for t in tables:
      print(format_table(t['id'], t['name'], t['columns']))
