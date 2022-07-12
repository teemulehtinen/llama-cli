from .MongodumpApi import MongodumpApi
from ..common import require

DEFAULT_TABLE_FILTERS = (
  ('==', 'user_instructor', True),
  ('==', 'user_assistant', True),
  ('!=', 'status', 'graded'),
)

DEFAULT_DATABASE_CONFIG = {
  'references_to_collections': ('{}', '{}s', 'submitted{}'),
  'module_key': 'round',
  'module_name_key': 'round',
  'table_key': 'exerciseId',
  'table_name_key': 'title',
  'time_key': 'received',
  'grade_key': 'points',
  'grade_max_key': 'grading_0_maxPoints',
  'pseudo_item_key': '_id',
  'pseudo_user_key': 'user__id',
  'table_filters': DEFAULT_TABLE_FILTERS,
  'drop_keys_re': '^(status|title|user_instructor|user_assistant|user_remoteUserId|user_customRole|grading_\d+__id|grading_\d+_feedback|files_\d+__id|fields___grader_lang)$',
  'show_keys_re': '^(fields_.+|files_.+_key)$',
  'personal_keys': ('user_name', 'user_email', 'user_studentId'),
}

def interactive_connect():
  print('This will add JSON files exported with Mongodump as a source for learning data.')
  main_file = input('Enter file paths to the data files: ')
  source_name = input('Enter a unique name to use for this source: ')
  require(main_file and source_name)
  source_id = ''.join(source_name.split())
  print('Edit .llama to adjust database field names from the defaults')
  return {
    'id': 'mongodump',
    'main_file': main_file,
    'source_id': source_id,
    'name': source_name,
    'database_config': DEFAULT_DATABASE_CONFIG,
  }

def construct_client(src):
  return MongodumpApi(src['source_id'], src['main_file'], src['database_config'])
