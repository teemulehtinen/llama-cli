TYPES = [ 'aplus' ]

def find_source(config, url):
  for s in config.sources:
    if s['url'] == url:
      return s
  return None

def command(args, config):
  if len(args) != 2 and len(args) != 3:
    print('Manages learning data sources for the working directory\n')
    print('usage: llama source <type> <url> [<token>]')
    print('   or: llama source rm <url>\n')
    print('Supported types are: {}'.format(', '.join(TYPES)))
    print('Tokens are stored separately to .tokens and ignored for git.')
  elif args[0] == 'rm':
    src = find_source(config, args[1])
    if src:
      config.set_sources(s for s in config.sources if s != src)
      print('Removed source: {} {}'.format(src['type'], src['url']))
    else:
      print('Source not found')
  elif args[0] in TYPES:
    src = {
      'type': args[0],
      'url': args[1],
    }
    if len(args) == 3:
      src['token'] = args[2]
    #TODO check source is valid
    old = find_source(config, args[1])
    if old:
      config.set_sources(s if s != old else src for s in config.sources)
    else:
      config.set_sources(config.sources + [src])
    print('Added source: {} {}'.format(src['type'], src['url']))
  else:
    print('Unknown source type')

def status(config):
  if config.sources:
    s = ''
    for i, src in enumerate(config.sources):
      s += 'Data source {:d}: {} {}\n'.format(i, src['type'], src['url'])
      return s
  else:
    return "No data sources configured"
