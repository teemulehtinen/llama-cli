from .types import enumerate_sources
from .list import format_source
from .common import require

def command(args, config):
  if not args in (['rows'], ['files']):
    print('Fetches learning data from sources\n')
    print('usage: llama fetch <target>\n')
    print('   rows      new table rows')
    print('   files     new file attachments for rows')
  else:
    for i, src, api in enumerate_sources(config):
      print(format_source(i, src['name']))
      tables, cached = api.list_tables(only_cache=True)
      require(cached, 'No table list loaded, use "list" command first')
      for t in tables:
        print(t)
