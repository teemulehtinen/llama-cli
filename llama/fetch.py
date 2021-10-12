from .types import get_sources_with_tables
from .Filters import Filters
from .common import write_json

def command(args, config):
  if not args in (['rows'], ['files']):
    print('Fetches learning data from sources\n')
    print('usage: llama fetch <target>\n')
    print('   rows      new table rows')
    print('   files     new file attachments for rows')
    print('   meta      TODO new meta attachments for rows')
  elif args == ['rows']:
    sources = get_sources_with_tables(config)
    fl = Filters(config.exclude)
    persons = fl.person_select(sources, config.privacy == 'none') if fl.has_person_filters() else None
    for s in fl.filter(sources):
      for t in s['tables']:
        s['api'].fetch_rows(t, config.privacy == 'none', False, persons, t['columns'])
  elif args == ['files']:
    fl = Filters(config.exclude)
    for s in fl.filter(get_sources_with_tables(config)):
      for t in s['tables']:
        rows, _ = s['api'].fetch_rows(t, only_cache=True)
        if rows is None:
          print(f'Skipping {t["name"]}: fetch rows first')
        else:
          for r in s['api'].fetch_files(t, rows, only_cache=True):
            if r['cached']:
              print(f'* Cached {r["row"][r["col"]]}')
