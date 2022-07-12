import random

from .types import get_sources_with_tables
from .Filters import Filters
from .Config import PERSON_KEY, EXPORT_DIR, EXPORT_INDEX_JSON
from .common import require, write_text, write_json, write_csv

def add_to_person_map(person_map, person_included, rows):
  for p in rows[PERSON_KEY]:
    if not p in person_map and (person_included is None or p in person_included):
      ap = None
      while ap is None or ap in person_map.values():
        ap = random.randint(1000, 9999)
      person_map[p] = ap

def command(args, config):
  sources = []
  person_map = {}
  person_included = Filters.person_included()
  fl = Filters(config.exclude)
  for s in fl.filter(get_sources_with_tables(config)):
    index_json = s['api'].table_list_json_name()
    sources.append({
      'name': s['name'],
      'type': s['type'],
      'index_file': '/'.join(index_json),
    })
    
    tables = []
    for t in s['tables']:
      rows, _ = s['api'].fetch_rows(t, only_cache=True)
      if rows is None:
        print(f'Skipping {t["name"]}: fetch rows first')
      else:
        add_to_person_map(person_map, person_included, rows)

        for r in s['api'].fetch_files(t, rows, only_cache=True):
          if not r['content'] is None:
            write_text((EXPORT_DIR,) + r['path'][1:], r['content'])

        metas = False
        for r in s['api'].fetch_meta(t, rows, only_cache=True):
          if not r['content'] is None:
            write_json((EXPORT_DIR,) + r['path'][1:], r['content'])
            metas = True

        table_csv = s['api'].table_csv_name(t['id'])[1:]
        export_rows = s['api'].export_rows(t, rows, person_map, metas, args)
        write_csv((EXPORT_DIR,) + table_csv, export_rows)
        tables.append({
          **t,
          'data_file': '/'.join(table_csv)
        })
        print(f'Anonymized {t["name"]}')
    
    write_json((EXPORT_DIR,) + index_json, tables)
  
  write_json((EXPORT_DIR, EXPORT_INDEX_JSON), {
    'llama': config.version,
    'sources': sources,
    'persons': Filters.person_status(),
  })
