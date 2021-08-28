from .types import Filters, get_sources_with_tables
from .list import format_source
from .common import require

def command(args, config):
  if not args in (['rows'], ['files']):
    print('Fetches learning data from sources\n')
    print('usage: llama fetch <target>\n')
    print('   rows      new table rows')
    print('   files     new file attachments for rows')
  elif args == ['rows']:
    fl = Filters().add(config.exclude)
    sources = fl.filter_columns(get_sources_with_tables(config))
    for s in sources:
      for t in s['tables']:
        s['api'].fetch_rows(t, config.privacy == 'none')
  elif args == ['files']:
    fl = Filters().add(config.exclude)
    sources = fl.filter_columns(get_sources_with_tables(config))
    for s in sources:
      for t in s['tables']:
        for r in s['api'].fetch_files(t, config.privacy == 'none'):
          if r['cached']:
            print(f'* Cached {r["row"][r["col"]]}')
