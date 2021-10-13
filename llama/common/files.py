import os
import json
import pandas

def path_to_file_name(path):
  return path if type(path) == str else os.path.join(*path)

def mkdir(dir_name):
  if not os.path.isdir(dir_name):
    os.mkdir(dir_name)

def ensure_dir(path):
  if type(path) != str:
    p = path[0]
    for i in range(0, len(path) - 1):
      mkdir(p)
      p = os.path.join(p, path[i + 1])

def read_text(path):
  file_name = path_to_file_name(path)
  if not os.path.isfile(file_name):
    return None
  with open(file_name) as f:
    return f.read()

def write_text(path, text):
  ensure_dir(path)
  with open(path_to_file_name(path), 'w') as f:
    f.write(text)

def read_json(path):
  text = read_text(path)
  return json.loads(text) if text else None

def write_json(path, data):
  write_text(path, json.dumps(data, indent=2))

def read_csv(path):
  file_name = path_to_file_name(path)
  if not os.path.isfile(file_name):
    return None
  return pandas.read_csv(file_name)

def write_csv(path, data):
  ensure_dir(path)
  data.to_csv(path_to_file_name(path), index=False)
