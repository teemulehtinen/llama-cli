from .common import find, require
from .config import Config
from . import status
from . import sources
from . import privacy
from . import consent

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
    'cmd': 'show',
    'desc': 'List available data tables and fields at source',
    'require': ['config', 'source'],
    'call': None,
  },
  {
    'cmd': 'privacy',
    'desc': 'Configure privacy (default: pseudoanonymous)',
    'call': privacy.command,
  },
  {
    'cmd': 'consent',
    'desc': 'Configure research consent field',
    'require': ['config', 'source'],
    'call': consent.command,
  },
  {
    'cmd': 'exclude',
    'desc': 'Exclude selected tables, fields, or rows (to optimize fetch)',
    'require': ['config', 'source'],
    'call': None,
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
