import random
from .config import PERSON_KEY
from .types import get_sources_with_tables
from .Filters import Filters
from .common import require

def add_to_person_map(person_map, person_included, rows):
  for p in rows[PERSON_KEY]:
    if not p in person_map and (person_included is None or p in person_included):
      ap = None
      while ap is None or ap in person_map.values():
        ap = random.randint(1000, 9999)
      person_map[p] = ap

def command(args, config):
  person_map = {}
  person_included = Filters.person_included()
  fl = Filters(config.exclude)
  for s in fl.filter(get_sources_with_tables(config)):
    for t in s['tables']:

      # Export table rows
      rows, _ = s['api'].fetch_rows(t, only_cache=True)
      if rows is None:
        print(f'Skipping {t["name"]}: fetch rows first')
      else:
        add_to_person_map(person_map, person_included, rows)
        rows[PERSON_KEY] = rows[PERSON_KEY].map(person_map)
        rows.dropna(subset=[PERSON_KEY], inplace=True)
        s['api'].write_export(t, rows)
        
        # Copy files
        #for r in s['api'].fetch_files(t, rows, only_cache=True):
        #  pass

        print(f'Anonymized {t["name"]}')
