from .AcosJsonApi import AcosJsonApi
from ..common import require

def interactive_connect():
  print('This will add JSON log files from ACOS-server as a source for learning data.')
  directory = input('Enter directory where to search for log files: ')
  source_name = input('Enter a unique name to use for this source: ')
  require(directory and source_name)
  source_id = ''.join(source_name.split())
  return {
    'id': 'acosjson',
    'directory': directory,
    'source_id': source_id,
    'name': source_name,
  }

def construct_client(src):
  return AcosJsonApi(src['source_id'], src['directory'])
