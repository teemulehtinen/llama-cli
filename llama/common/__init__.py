import sys
from .input import *

def find(items, condition):
  return next((i for i in items if condition(i)), None)

def require(condition, message='Cancelled', exit_code=0):
  if not condition:
    print(message)
    sys.exit(exit_code)
