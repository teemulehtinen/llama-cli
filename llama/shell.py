import code
from .LlamaApi import LlamaApi
from .common import require

def command(args, config):
  code.interact('Use "llama" to access data', local={
    'llama': LlamaApi(*args),
  })
