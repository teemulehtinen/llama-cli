from .common import require, input_selection
from .types import TYPES, interactive_add

def command(args, config):
  if not args in (['add'], ['rm']):
    print('Manages learning data sources for the working directory\n')
    print('usage: llama source <op>\n')
    print('   add       Add a new source, interactive options')
    print('   rm        Remove a source, interactive selection')
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
    src = interactive_add(TYPES[i])
    if src:
      config.set_sources(config.sources + [src])
      print(f'Added source: {src["name"]}')
