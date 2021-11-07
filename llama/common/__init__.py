import sys
from .input import *
from .files import *
from .dataframes import *

def require(condition, message='Cancelled', exit_code=0):
  if not condition:
    print(message)
    sys.exit(exit_code)

def print_updated_line(line):
  sys.stdout.write('\r' + line)
  sys.stdout.flush()

def find(items, condition):
  return next((i for i in items if condition(i)), None)

def count(iterator):
  return sum(1 for a in iterator)

def as_list(param):
  if type(param) == list:
    return param
  if type(param) == tuple:
    return list(param)
  return [param]

def flatten_dict(d):
  r = {}
  for k, v in d.items():
    if type(v) == dict:
      for k2, v2 in v.items():
        r[f'{k}_{k2}'] = v2
    elif type(v) == list:
      for i, v2 in enumerate(v):
        r[f'{k}_{i}'] = v2
    else:
      r[k] = v
  return r
