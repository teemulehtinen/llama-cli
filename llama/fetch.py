from .types import get_sources_with_tables
from .Filters import Filters
from .common import write_json

def get_filtered_table_rows(config):
  fl = Filters(config.exclude)
  for s in fl.filter(get_sources_with_tables(config)):
    for t in s['tables']:
      rows, _ = s['api'].fetch_rows(t, only_cache=True)
      if rows is None:
        print(f'Skipping {t["name"]}: fetch rows first')
      else:
        yield s, t, rows

def command(args, config):
  if not args in (['rows'], ['files'], ['meta']):
    print('Fetches learning data from sources\n')
    print('usage: llama fetch <target>\n')
    print('   rows      new table rows')
    print('   files     new file attachments for rows')
    print('   meta      new meta attachments for rows')
  elif args == ['rows']:
    sources = get_sources_with_tables(config)
    fl = Filters(config.exclude)
    persons = fl.person_select(sources, config.privacy == 'none') if fl.has_person_filters() else None
    for s in fl.filter(sources):
      for t in s['tables']:
        columns_rm = [c['key'] for c in t['columns_rm']] if 'columns_rm' in t else None
        s['api'].fetch_rows(t, config.privacy == 'none', False, persons, columns_rm)
  elif args == ['files']:
    for source, table, rows in get_filtered_table_rows(config):
      for r in source['api'].fetch_files(table, rows, config.privacy == 'none'):
        if r['cached']:
          print(f'* Cached file {"/".join(r["path"])}')
  elif args == ['meta']:
    for source, table, rows in get_filtered_table_rows(config):
      for r in source['api'].fetch_meta(table, rows, config.privacy == 'none'):
        if r['cached']:
          print(f'* Cached meta {"/".join(r["path"])}')
