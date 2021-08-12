import sys
from . import llama

if len(sys.argv) < 2:
  print('Llama CLI fetches and preprocesses learning data\n')
  print('usage: llama <cmd> [<args>]\n')
  print('   status    Show the working tree status')
  print('   source    Manage sources for learning data')
  print('   show      List available data schema at source')
  print('   privacy   Configure privacy (default: pseudoanonymous)')
  print('   consent   Configure research consent field')
  print('   fetch     Fetch data entries from source')
  sys.exit(0)

llama(sys.argv[1], sys.argv[2:])

