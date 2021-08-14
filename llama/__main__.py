import sys
from . import COMMANDS, llama_cli

if len(sys.argv) < 2:
  print('Llama CLI fetches and preprocesses learning data\n')
  print('usage: llama <cmd> [<args>]\n')
  for c in COMMANDS:
    print(f'   {c["cmd"]: <10}{c["desc"]}')
  sys.exit(0)

llama_cli(sys.argv[1], sys.argv[2:])
