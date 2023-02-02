from .types import get_sources_with_tables
from .Filters import Filters
from .common import require

def get_filtered_table_rows(select_filter, config):
  fl = Filters(config.exclude)
  for s in select_filter.filter(fl.filter(get_sources_with_tables(config))):
    for t in s['tables']:
      rows, _ = s['api'].fetch_rows(t, only_cache=True)
      if rows is None:
        print(f'Skipping {t["name"]}: fetch rows first')
      else:
        yield s, t, rows

def command(args, config):
  target = args[0] if len(args) > 0 else None
  if not target in ('rows', 'files', 'meta'):
    print('Fetches learning data from sources\n')
    print('usage: llama fetch <target> [<select>]\n')
    print('   target    rows     new table rows')
    print('             files    new file attachments for rows')
    print('             meta     new meta attachments for rows')
    print('   select    [-][source:](#table_id|partial_table_name)')
    return
  fls = Filters([], inclusive=True)
  if len(args) > 1:
    select = Filters.parse(' '.join(args[1:]), columns=False)
    require(select, 'Invalid select pattern')
    fls.add([select])
  if target == 'rows':
    sources = get_sources_with_tables(config)
    fl = Filters(config.exclude)
    persons = fl.person_select(sources, config.privacy == 'none') if fl.has_person_filters() else None
    for s in fls.filter(fl.filter(sources)):
      for t in s['tables']:
        columns_rm = [c['key'] for c in t['columns_rm']] if 'columns_rm' in t else None
        s['api'].fetch_rows(t, config.privacy == 'none', False, persons, columns_rm)
  elif target == 'files':
    for source, table, rows in get_filtered_table_rows(fls, config):
      for r in source['api'].fetch_files(table, rows, config.privacy == 'none'):
        if r['cached']:
          print(f'* Cached file {"/".join(r["path"])}')
  elif target == 'meta':
    for source, table, rows in get_filtered_table_rows(fls, config):
      for r in source['api'].fetch_meta(table, rows, config.privacy == 'none'):
        if r['cached']:
          print(f'* Cached meta {"/".join(r["path"])}')
