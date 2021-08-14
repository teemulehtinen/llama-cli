from .common import require, input_selection
from .types import TYPES, select_type

def command(args, config):
  if not args in (['add'], ['rm']):
    print('Manages learning data sources for the working directory\n')
    print('usage: llama source add')
    print('   or: llama source rm\n')
  elif args == ['rm']:
    require(config.sources, 'No data sources configured')
    print('Consider sources for removal')
    i = input_selection(s['name'] for s in config.sources)
    require(not i is None)
    src = config.sources[i]
    config.set_sources(s for j, s in enumerate(config.sources) if j != i)
    print(f'Removed source: {src["name"]}')
  elif args == ['add']:
    print('Available data source types')
    i = input_selection(t['name'] for t in TYPES)
    require(not i is None)
    type = TYPES[i]
    src = type['add']()
    if src:
      config.set_sources(config.sources + [src])
      print(f'Added source: {src["name"]}')

def status(config):
  if not config.sources:
    return "No data sources configured"
  lines = []
  for i, src in enumerate(config.sources):
    lines.append(f'Source {i:d} [{src["id"]}] {src["name"]}')
    #TODO display item count and time period
  return '\n'.join(lines)
