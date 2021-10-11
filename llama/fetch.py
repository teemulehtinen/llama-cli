from llama.common.files import write_json
from .types import get_sources_with_tables
from .list import format_source
from .common import require, Filters

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
    if fl.has_person_filters():
      persons = fl.person_select(sources, config.privacy == 'none')
    for s in fl.filter(sources):
      for t in s['tables']:
        s['api'].fetch_rows(t, config.privacy == 'none', False, persons, t['columns'])
  elif args == ['files']:
    fl = Filters(config.exclude)
    for s in fl.filter(get_sources_with_tables(config)):
      for t in s['tables']:
        rows, _ = s['api'].fetch_rows(t, config.privacy == 'none', True)
        if rows is None:
          print(f'Skipping {t["name"]}: fetch rows first')
        else:
          for r in s['api'].fetch_files(t, rows, config.privacy == 'none'):
            if r['cached']:
              print(f'* Cached {r["row"][r["col"]]}')
