from . import exclude
from . import privacy
from .types import enumerate_sources
from .common import require

def status_sources(config):
  if not config.sources:
    return "No data sources configured"
  lines = []
  for i, src, api in enumerate_sources(config):
    lines.append(f'{i:d}: {src["name"]} [{src["id"]}]')
    tables, cached = api.list_tables(only_cache=True)
    if cached:
      lines.append(f'   {len(tables):d} tables')
      #TODO row count, date
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
  llama = 8 #TODO Llama instance
  code.interact(status(config), local=locals())