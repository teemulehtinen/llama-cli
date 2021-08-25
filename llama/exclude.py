import re
from .types import Filters, get_sources_with_tables
from .list import format_source, format_table
from .common import require, input_selection

def parse_exclusion(pattern):
  result = re.match(r'^(-)?(\d+:)?(#?[\w ]+)?(\.[\w ]+)?(=[\w ]+)?$', pattern)
  if not result:
    return None
  re_groups = result.groups()
  table_id = re_groups[2] and re_groups[2].startswith('#')
  return {
    'reverse': re_groups[0] == '-',
    'source': int(re_groups[1][:-1]) if re_groups[1] else None,
    'table_by_id': table_id,
    'table': re_groups[2][1:] if table_id else re_groups[2],
    'column': re_groups[3][1:] if re_groups[3] else None,
    'value': re_groups[4][1:] if re_groups[4] else None,
  }

def format_exclusion(spec):
  reverse = '-' if spec['reverse'] else ''
  source = f'{spec["source"]}:' if not spec['source'] is None else ''
  table = f'{"#" if spec["table_by_id"] else ""}{spec["table"]}' if spec['table'] else ''
  column = f'.{spec["column"]}' if spec['column'] else ''
  value = f'={spec["value"]}' if spec['value'] else ''
  return f'"{reverse}{source}{table}{column}{value}"'

def print_matches(sources):
  for s in sources:
    if s['match']:
      print(format_source(s['id'], s['name']))
      for t in s['tables']:
        if t['match']:
          print(format_table(t['id'], t['name'], [c for c in t['columns'] if c['match']]))

def command(args, config):
  if not args in (['rm'], ['apply']) and (len(args) < 2 or not args[0] in ('test', 'set')):
    print('Excludes data before or during fetching from the source')
    print('Data selections for analysis follow later and are not exclusions!\n')
    print('usage: llama exclude test "[-][<source>:][[#]<table>][.<column>[=<value>]]"')
    print('       llama exclude set "[-][<source>:][[#]<table>][.<column>[=<value>]]"')
    print('       llama exclude rm')
    print('       llama exclude apply\n')
    print('       test       Test exclusion without storing it')
    print('       set        Set new exclusion')
    print('       rm         Remove exclusion, interactive selection')
    print('       apply      Test applying all exclusions\n')
    print('       -part-     -example-   -description-')
    print('                  -           excludes everything NOT specified in the rest')
    print('       source     0:          selects source by the index')
    print('       table      #123        selects table by the id')
    print('                  feedback    selects table by text included in the name')
    print('       column     .field_1    selects column by text included in the name')
    print('       value      =yes        selects users by text included in the column\n')
    print('       llama exclude set #424.secret')
    print('       llama exclude set "-research consent=yes"\n')
    print('Note that whole tables or columns in any table can be selected by omitting')
    print('other parts in the specification. Value-part is used to select persons whose')
    print('rows are then excluded in all tables.')
  elif args == ['rm']:
    require(config.exclude, 'No exclusions configured')
    print('Consider exclusion for removal')
    i = input_selection(format_exclusion(e) for e in config.exclude)
    require(not i is None)
    exc = config.exclude[i]
    config.set_exclude(e for j, e in enumerate(config.exclude) if j != i)
    print(f'Removed exclusion: {format_exclusion(exc)}')
  elif args == ['apply']:
    fl = Filters().add(config.exclude)
    sources = fl.filter_columns(get_sources_with_tables(config))
    print_matches(sources)
  else:
    exc = parse_exclusion(' '.join(args[1:]))
    require(exc, 'Invalid exclude pattern')
    if exc['source']:
      require(0 <= exc['source'] < len(config.sources), 'Invalid source index')
    fl = Filters(False).add([exc])
    sources = fl.filter_columns(get_sources_with_tables(config))
    print_matches(sources)
    #print(f'   {len(excluded):d}/{len(tables):d} tables in exclusion')
    if exc['value']:
      if exc['reverse']:
        print(f'*** users not having "{exc["value"]}" in each of the above columns')
      else:
        print(f'*** users having "{exc["value"]}" in any of the above columns')
    if args[0] == 'set':
      config.set_exclude(config.exclude + [exc])
      print(f'Added exclusion: {format_exclusion(exc)}')

def status(config):
  if config.exclude:
    return ' '.join(['Exclude:'] + [format_exclusion(e) for e in config.exclude])
  return None
