PRIVACY_TXT = {
  'pseudo': 'Data is pseudoanonymized during load, use "anonymize" to export',
  'none': 'Data includes PERSONAL INFORMATION - protect it!'
}

def command(args, config):
  if len(args) != 1:
    print('Direct personal identifiers are removed on load by default\n')
    print('usage: llama privacy <mode>\n')
    print('   pseudo   Pseudoanonymous identifiers are kept. With access to the source')
    print('            system, the data can be tracked back to real identities.\n')
    print('   none     Personal information including e.g. names and emails is kept. Only')
    print('            for course administrative tasks in a properly secured media.\n')
    print(f'Current: {config.privacy}')
  elif args[0] in PRIVACY_TXT:
    config.set_privacy(args[0])
    print(f'Privacy mode set to: {config.privacy}')
  else:
    print('Not a privacy mode')

def status(config):
  return PRIVACY_TXT.get(config.privacy, 'ERROR: unknown privacy setting')
