import random
from .types import get_sources_with_tables
from .Filters import Filters
from .Config import PERSON_KEY, EXPORT_DIR, EXPORT_INDEX_JSON, VERSION
from .common import require, write_text, write_json

def add_to_person_map(person_map, person_included, rows):
  for p in rows[PERSON_KEY]:
    if not p in person_map and (person_included is None or p in person_included):
      ap = None
      while ap is None or ap in person_map.values():
        ap = random.randint(1000, 9999)
      person_map[p] = ap

def command(args, config):
  require(args == [], 'Unknown command')
  sources = []
  person_map = {}
  person_included = Filters.person_included()
  fl = Filters(config.exclude)
  for s in fl.filter(get_sources_with_tables(config)):
    sources.append({
      'name': s['name'],
      'type': s['type'],
      'index': '/'.join(s['index']),
    })
    write_json((EXPORT_DIR,) + s['index'], s['tables'])
    for t in s['tables']:
      rows, _ = s['api'].fetch_rows(t, only_cache=True)
      if rows is None:
        print(f'Skipping {t["name"]}: fetch rows first')
      else:
        add_to_person_map(person_map, person_included, rows)
        for r in s['api'].fetch_files(t, rows, only_cache=True):
          if not r['content'] is None:
            write_text((EXPORT_DIR,) + r['path'][1:], r['content'])
        for r in s['api'].fetch_meta(t, rows, only_cache=True):
          if not r['content'] is None:
            write_json((EXPORT_DIR,) + r['path'][1:], r['content'])
        s['api'].write_export(t, rows, person_map)
        print(f'Anonymized {t["name"]}')
  write_json((EXPORT_DIR, EXPORT_INDEX_JSON), {
    'llama': VERSION,
    'sources': sources,
    'persons': Filters.person_status(),
  })
