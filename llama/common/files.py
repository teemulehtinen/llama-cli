import os
import json
import pandas

def read_file(file_name):
  with open(file_name) as f:
    return f.read()

def write_file(file_name, text):
  with open(file_name, 'w') as f:
    f.write(text)

def read_json(file_name):
  if not os.path.isfile(file_name):
    return None
  return json.loads(read_file(file_name))

def write_json(file_name, data):
  write_file(file_name, json.dumps(data, indent=2))

def read_csv(file_name):
  if not os.path.isfile(file_name):
    return None
  return pandas.read_csv(file_name)

def write_csv(file_name, data):
  data.to_csv(file_name, index=False)
