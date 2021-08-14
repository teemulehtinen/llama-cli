def consent_str(consent):
  return ' '.join(consent) if consent else 'none'

def command(args, config):
  if args != ['none'] and len(args) != 3:
    print('Configures a source field to exclude learners who did not consent')
    print('e.g. the field contains a yes-answer to research consent statement\n')
    print('usage: llama consent <item> <field> <value>')
    print('   or: llama consent none\n')
    print(f'Current: {consent_str(config.consent)}')
  elif args == ['none']:
    config.set_consent(None)
    print('Conset set to: none')
  else:
    config.set_consent(args)
    print(f'Consent set to: {consent_str(config.consent)}')

def status(config):
  return f'Filter by consent field: {consent_str(config.consent)}'
