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
