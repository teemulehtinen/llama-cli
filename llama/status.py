from llama.Llama import Llama
from . import exclude
from . import privacy
from .types import enumerate_sources, get_sources_with_tables
from .common import require, print_updated_line, count

def status_sources(config):
  if not config.sources:
    return "No data sources configured"
  lines = []
  for i, src, api in enumerate_sources(config):
    lines.append(f'{i:d}: {src["name"]} [{src["id"]}]')
    tables, cached = api.list_tables(only_cache=True)
    if cached:
      table_n = len(tables)
      row_n = 0
      file_n = 0
      print_updated_line(f'   0 %')
      for i, t in enumerate(tables):
        rows, _ = api.fetch_rows(t, only_cache=True)
        row_n += 0 if rows is None else rows.shape[0]
        file_n += count(api.fetch_files(t, only_cache=True))
        print_updated_line(f'   {int(100 * i / table_n)} %')
      print_updated_line('')
      lines.append(f'   {table_n} tables, {row_n} rows & {file_n} files fetched')
    else:
      lines.append('   No table list loaded, use "list" command')
  return '\n'.join(lines)

def status(config):
  lines = [
    f'Llama {config.version} ~ la lumière à Montagne analytique',
    '',
    status_sources(config),
    '',
    exclude.status(config),
    privacy.status(config)
  ]
  return '\n'.join(l for l in lines if not l is None)

def command(args, config):
  require(args == [], 'Unknown command')
  print(status(config))

def shell(args, config):
  require(args == [], 'Unknown command')
  import code
  code.interact('Use "llama" to access data', local={
    'llama': Llama(config),
  })
