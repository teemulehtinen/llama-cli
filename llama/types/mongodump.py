from .MongodumpApi import MongodumpApi
from ..common import require, input_selection

def interactive_connect():
  print('This will add JSON files exported with Mongodump as a source for learning data.')
  main_file = input('Enter file path to the main data file: ')
  source_name = input('Enter a unique name to use for this source: ')
  require(main_file and source_name)
  source_id = ''.join(source_name.split())
  MongodumpApi.create(source_id, main_file)
  return {
    'id': 'mongodump',
    'main_file': main_file,
    'source_id': source_id,
    'name': source_name,
  }

def construct_client(src):
  return MongodumpApi(src['source_id'], src['main_file'])
