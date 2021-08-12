from posixpath import join
from .config import Config
from . import sources
from . import privacy
from . import consent

VERSION = '1.0.0'

def llama(command, args):
  config = Config(VERSION)
  if command == 'source':
    sources.command(args, config)
  elif command == 'privacy':
    privacy.command(args, config)
  elif command == 'consent':
    consent.command(args, config)
  elif not config.exists:
    print('The working directory has no configuration (.llama)')
  elif command == 'status':
    print('Llama {} ~la lumière à Montagne analytique~\n'.format(config.version))
    print(sources.status(config))
    if config.consent:
      print(consent.status(config))
    print(privacy.status(config))

  elif command == 'show':
    print('TODO')
  
  elif command == 'fetch':
    print('TODO')
  
  else:
    print('Uknown command')
