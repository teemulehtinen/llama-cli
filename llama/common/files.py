import os
import json
import pandas

def read_text(file_name):
  if not os.path.isfile(file_name):
    return None
  with open(file_name) as f:
    return f.read()

def write_text(file_name, text):
  with open(file_name, 'w') as f:
    f.write(text)

def read_json(file_name):
  text = read_text(file_name)
  return json.loads(text) if text else None

def write_json(file_name, data):
  write_text(file_name, json.dumps(data, indent=2))

def read_csv(file_name):
  if not os.path.isfile(file_name):
    return None
  return pandas.read_csv(file_name)

def write_csv(file_name, data):
  data.to_csv(file_name, index=False)

def mkdir(dir_name):
  if not os.path.isdir(dir_name):
    os.mkdir(dir_name)

def ensure_dir_and_write_text(path_parts, content):
  if not content is None:
    path = path_parts[0]
    for i in range(0, len(path_parts) - 1):
      mkdir(path)
      path = os.path.join(path, path_parts[i + 1])
    write_text(path, content)
