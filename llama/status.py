from . import sources
from . import consent
from . import privacy

def status(config):
  lines = [
    f'Llama {config.version} ~ la lumière à Montagne analytique',
    '',
    sources.status(config),
    '',
    consent.status(config) if config.consent else None,
    privacy.status(config)
  ]
  return '\n'.join(l for l in lines if not l is None)

def command(args, config):
  print(status(config))

def shell(args, config):
  import code
  llama = 8 #TODO Llama instance
  code.interact(status(config), local=locals())
