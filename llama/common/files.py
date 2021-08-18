import os
import json

def read_file(file_name):
  with open(file_name) as f:
    return f.read()

def read_json(file_name):
  if not os.path.isfile(file_name):
    return {}
  return json.loads(read_file(file_name))

def write_file(file_name, text):
  with open(file_name, 'w') as f:
    f.write(text)

def write_json(file_name, data):
  write_file(file_name, json.dumps(data, indent=2))
