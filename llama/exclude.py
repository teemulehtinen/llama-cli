from llama.list import format_source, format_table
import re
from .types import enumerate_sources
from .common import require

def match_source(spec, source):
  if spec['source'] is None:
    return True
  if spec['reverse']:
    return spec['source'] != source
  return spec['source'] == source

def match_table(spec, table):
  def check(table):
    if spec['table_by_id']:
      return spec['table'] == str(table['id'])
    return spec['table'] in table['name']
  if spec['table'] is None:
    return True
  if spec['reverse']:
    return not check(table)
  return check(table)

def match_columns(spec, table):
  def check(column):
    if spec['column'] is None:
      return True
    if spec['reverse']:
      return not spec['column'] in column
    return spec['column'] in column
  return [c for c in table['columns'] if check(c)]

def match(spec, source, tables):
  excluded = []
  if match_source(spec, source):
    for t in tables:
      if match_table(spec, t):
        cols = t['columns'] if spec['reverse'] else match_columns(spec, t)
      elif spec['reverse'] and spec['column']:
        cols = match_columns(spec, t)
      else:
        cols = []
      if cols:
        excluded.append({ 'table': t, 'columns': cols })
  return excluded

def command(args, config):
  if args != ['rm'] and (len(args) < 2 or not args[0] in ('test', 'set')):
    print('Excludes data before or during fetching from the source')
    print('Data selections for analysis follow later and are not exclusions!\n')
    print('usage: llama exclude test "[-][<source>:][[#]<table>][.<column>[=<value>]]"')
    print('       llama exclude set "[-][<source>:][[#]<table>][.<column>[=<value>]]"')
    print('       llama exclude rm\n')
    print('       test       Test exclusion without storing it')
    print('       set        Set new exclusion')
    print('       rm         Remove exclusion, interactive selection\n')
    print('       -part-     -example-   -description-')
    print('                  -           excludes everything NOT specified in the rest')
    print('       source     0:          selects source by the index')
    print('       table      #123        selects table by the id')
    print('                  feedback    selects table by text included in the name')
    print('       column     .field_1    selects column by text included in the name')
    print('       value      =yes        selects users by text included in the column\n')
    print('       llama "-#424.my column=yes please"\n')
    print('Note that whole tables or columns in any table can be selected by omitting')
    print('other parts in the specification. Value is used to select persons whose rows')
    print('are then excluded in all tables.')
  elif args == ['rm']:
    print('TODO rm from list')
  else:
    pattern = ' '.join(args[1:])
    result = re.match(r'^(-)?(\d+:)?(#?[\w ]+)?(\.[\w ]+)?(=[\w ]+)?$', pattern)
    require(result, 'Invalid exclude pattern')
    re_groups = result.groups()
    table_id = re_groups[2] and re_groups[2].startswith('#')
    exclude = {
      'reverse': re_groups[0] == '-',
      'source': int(re_groups[1][:-1]) if re_groups[1] else None,
      'table_by_id': table_id,
      'table': re_groups[2][1:] if table_id else re_groups[2],
      'column': re_groups[3][1:] if re_groups[3] else None,
      'value': re_groups[4][1:] if re_groups[4] else None,
    }
    if exclude['source']:
      require(0 <= exclude['source'] < len(config.sources), 'Invalid source index')
    for i, src, api in enumerate_sources(config):
      print(format_source(i, src['name']))
      tables, cached = api.list_tables(only_cache=True)
      require(cached, 'No table list loaded, use "list" command first')
      excluded = match(exclude, i, tables)
      for e in excluded:
        print(format_table(e['table']['id'], e['table']['name'], e['columns']))
      print(f'   {len(excluded):d}/{len(tables):d} tables in exclusion')
    if exclude['value']:
      print(f'*** users having "{exclude["value"]}" in any of the above columns')
    if args[0] == 'set':
      print('TODO store')

def consent_str(consent):
  return ' '.join(consent) if consent else 'none'

def command_consent(args, config):
  if args != ['none'] and len(args) != 3:
    print('Configures a source field to exclude learners who did not consent')
    print('e.g. the field contains a yes-answer to research consent statement\n')
    print('usage: llama consent <item> <field> <value>')
    print('   or: llama consent none\n')
    print(f'Current: {consent_str(config.consent)}')
  elif args == ['none']:
    config.set_consent(None)
    print('Conset set to: none')
  else:
    config.set_consent(args)
    print(f'Consent set to: {consent_str(config.consent)}')

def status(config):
  lines = []
  #TODO all exlusions
  if config.consent:
    lines.append(f'Filter by consent field: {consent_str(config.consent)}')
  return lines or None
