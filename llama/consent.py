def command(args, config):
  if len(args) != 3 and (len(args) != 1 or args[0] != 'none'):
    print('Configures a source field that filters data by learner\'s consent')
    print('e.g. the field contains a yes-answer to research consent statement\n')
    print('usage: llama consent <item> <field> <value>')
    print('   or: llama consent none\n')
    print('Current: {}'.format(' '.join(config.consent) if config.consent else 'none'))
  elif len(args) == 1:
    config.set_consent(None)
    print('Conset set to: none')
  else:
    config.set_consent(args)
    print('Consent set to: {}'.format(' '.join(config.consent)))

def status(config):
  return 'Filter by consent field: {}\n'.format(' '.join(config.consent))
