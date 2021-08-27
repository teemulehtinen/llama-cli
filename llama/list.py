from .types import enumerate_sources

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
        print(format_table(t['id'], t['name'], t['columns']))
