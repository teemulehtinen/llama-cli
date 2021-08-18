from .common import find, require
from .config import Config
from . import status
from . import sources
from . import list
from . import privacy
from . import exclude

VERSION = '1.0.0'

COMMANDS = [
  {
    'cmd': 'status',
    'desc': 'Show the working tree status',
    'require': ['config'],
    'call': status.command,
  },
  {
    'cmd': 'source',
    'desc': 'Manage sources for learning data',
    'call': sources.command,
  },
  {
    'cmd': 'list',
    'desc': 'List available data tables and columns',
    'require': ['config', 'source'],
    'call': list.command,
  },
  {
    'cmd': 'privacy',
    'desc': 'Configure privacy (default: pseudoanonymous)',
    'call': privacy.command,
  },
  {
    'cmd': 'exclude',
    'desc': 'Exclude selected tables, columns, or persons at fetch',
    'require': ['config', 'source'],
    'call': exclude.command,
  },
  {
    'cmd': 'fetch',
    'desc': 'Fetch data from sources',
    'require': ['config', 'source'],
    'call': None,
  },
  {
    'cmd': 'shell',
    'desc': 'Open python REPL with \'llama\' instance to fetched data',
    'require': ['config', 'source'],
    'call': status.shell,
  }
]

def llama_cli(cmd, args):
  definition = find(COMMANDS, lambda c: c['cmd'] == cmd)
  require(definition, 'Unknown command')
  config = Config(VERSION)
  requirements = definition.get('require', [])
  if 'config' in requirements:
    require(config.exists, 'The working directory has no configuration (.llama)')
  if 'source' in requirements:
    require(config.sources, 'First, use command \'source\' to configure a data source')
  require(definition.get('call', None), 'FATAL: command missing implementation', 1)
  definition['call'](args, config)
