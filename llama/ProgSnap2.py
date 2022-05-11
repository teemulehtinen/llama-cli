import re
import json
import os
import pandas

from .common import read_text, mkdir
from .Config import GRADE_KEY, PERSON_KEY, TIME_KEY
from .types.AplusApi import AplusApi

class ProgSnap2:

  def __init__(self, selection, export_dir):
    self.selection = selection
    self.export_dir = export_dir
    self.file_key_re = re.compile(AplusApi.FILE_KEY_REGEXP)
    self.main_table = pandas.DataFrame()
    self.code_table = pandas.DataFrame()
    self.code_id_count = 1
    self.unknown_code_id = None

  def append_codestate(self, code):
    code_id = self.code_id_count
    self.code_table = pandas.concat(
      [self.code_table, pandas.DataFrame([{ 'CodeStateID': code_id, 'Code': code, }])],
      ignore_index=True
    )
    self.code_id_count += 1
    return code_id

  def unknown_codestate(self):
    if self.unknown_code_id is None:
      self.unknown_code_id = self.append_codestate('Not saved')
    return self.unknown_code_id
  
  def append_event(self, dict):
    self.main_table = pandas.concat(
      [self.main_table, pandas.DataFrame([dict])],
      ignore_index=True
    )
  
  def ms_timestamp(self, ms):
    return pandas.Timestamp(ms, unit='ms')

  def process(self):
    for source, table, rows in self.selection:
      print(f'Processing {source["name"]}:{table["name"]}')

      tool_instance = 'Unknown'
      file_path_columns = None
      file_content_columns = None
      log_column = None
      if source['type'] == 'aplus':
        tool_instance = 'Aplus'
        file_path_columns = list(c for c in rows.columns if self.file_key_re.match(c))
      elif source['type'] == 'mongodump':
        file_content_columns = list(c for c in rows.columns if c.endswith('_contents'))
      elif source['type'] == 'acosjson':
        tool_instance = 'Acos'
        log_column = 'log' if 'log' in rows.columns else None

      for _, row in rows.iterrows():
        defs = {
          'ToolInstances': tool_instance,
          'AssignmentID': table['id'],
          'ServerTimestamp': row[TIME_KEY].isoformat(timespec='seconds'),
          'SubjectID': row[PERSON_KEY],
        }

        code_id = None
        if file_path_columns:
          code_id = self.append_codestate('\n'.join(read_text(row[c]) for c in file_path_columns))
        elif file_content_columns:
          code_id = self.append_codestate('\n'.join(row[c] for c in file_content_columns))

        if log_column:
          code_id = code_id or self.unknown_codestate()
          qlcs = None
          for event in json.loads(row[log_column]):
            type = event.get('type')
            if type == 'editor-change' and event.get('action') in ('insert', 'remove'):
              is_insert = event['action'] == 'insert'
              self.append_event({
                **defs,
                'ClientTimestamp': self.ms_timestamp(event['time']).isoformat(timespec='seconds'),
                'EventType': 'File.Edit',
                'CodeStateID': code_id,
                'EditType': 'Insert' if is_insert else 'Remove',
                'SourceLocation': f'Text:{event["start"]["row"]}:{event["start"]["column"]}',
                'X-InsertText': '\n'.join(event['lines']) if is_insert else None,
                'X-DeleteText': '\n'.join(event['lines']) if not is_insert else None,
              })
            elif type == 'qlc-init':
              qlcs = event.get('qlcs')
            elif type == 'qlc-select':
              self.append_event({
                **defs,
                'ClientTimestamp': self.ms_timestamp(event['time']).isoformat(timespec='seconds'),
                'EventType': 'X-QLC.Answer',
                'CodeStateID': code_id,
                'X-QLC.Type': qlcs[event['qlc']]['qlctype'],
                'X-QLC.AnswerType': event['option']['qlctype'],
                'X-QLC.AnswerText': event['option']['answer'],
                'Score': 1 if event['option'].get('correct', False) else 0,
              })

          if not log_column or row.get('status') == 'graded':
            self.append_event({
              **defs,
              'EventType': 'Submit',
              'CodeStateID': code_id or self.unknown_codestate(),
              'Score': row[GRADE_KEY],
            })

  def write(self):
    if not self.main_table.empty:
      mkdir(self.export_dir)
      pandas.DataFrame({
        'Property': ['Version', 'CodeStateRepresentation'],
        'Value': [6, 'Table'],
      }).to_csv(os.path.join(self.export_dir, 'DatasetMetadata.csv'), index=None)
      self.main_table.index.names = ['EventID']
      self.main_table.to_csv(os.path.join(self.export_dir, 'MainTable.csv'))
      if not self.code_table.empty:
        self.code_table.to_csv(os.path.join(self.export_dir, 'CodeStates.csv'), index=None)
