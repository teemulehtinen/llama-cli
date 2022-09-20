import unittest

from llama.Filters import Filters

SOURCES = [
  {
    'id': 0,
    'tables': [
      {
        'id': 'T1',
        'name': 'T1',
        'columns': [{ 'key': 'fields_a' }, { 'key': 'fields_b' }],
      },
      {
        'id': 'T2',
        'name': 'T2',
        'columns': [{ 'key': 'fields_b' }, { 'key': 'fields_c' }],
      }
    ],
  },
  {
    'id': 1,
    'tables': [
      {
        'id': 'T3',
        'name': 'T3',
        'columns': [],
      },
    ],
  },
]

def table_ids(sources):
  return list(t['id'] for s in sources for t in s['tables'])

def columns(sources, table_id):
  for s in sources:
    for t in s['tables']:
      if t['id'] == table_id:
        return t['columns']
  return None

class TestFilters(unittest.TestCase):

  def test_empty(self):
    fl = Filters()
    self.assertSequenceEqual(table_ids(fl.filter(SOURCES)), ['T1', 'T2', 'T3'])

  def test_exclusion_table(self):
    fl = Filters([{ 'source': 0, 'table': 'T2', 'table_by_id': True }])
    self.assertSequenceEqual(table_ids(fl.filter(SOURCES)), ['T1', 'T3'])
  
  def test_exclusion_table_name(self):
    fl = Filters([{ 'table': 'T' }])
    self.assertSequenceEqual(table_ids(fl.filter(SOURCES)), [])

  def test_inclusion_table(self):
    fl = Filters([{ 'table': 'T2', 'table_by_id': True, 'column': 'fields_b' }], inclusive=True)
    self.assertSequenceEqual(table_ids(fl.filter(SOURCES)), ['T2'])

  def test_inclusion_name(self):
    fl = Filters([{ 'source': 0, 'table': '1' }], inclusive=True)
    self.assertSequenceEqual(table_ids(fl.filter(SOURCES)), ['T1'])

if __name__ == '__main__':
  unittest.main()
