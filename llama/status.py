from .types import enumerate_sources
from .Llama import Llama
from .common import require
from . import exclude
from . import privacy

def status_sources(config):
  if not config.sources:
    return "No data sources configured"
  lines = []
  for i, src, api in enumerate_sources(config):
    tables, cached = api.list_tables(only_cache=True)
    lines.append(f'{i:d}: {src["name"]} [{src["type"]}]')
    if cached:
      lines.append(f'   {len(tables)} tables')
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
