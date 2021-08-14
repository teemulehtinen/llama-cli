#!/usr/bin/env python3
import os
import requests
import json
import pandas as pd


class AplusQuery(object):

    @classmethod
    def get(cls, url, api_key):
        print('Aplus API GET', url)
        return requests.get(url, headers={'Authorization': 'Token ' + api_key})

    @classmethod
    def read_url(cls, url, api_key):
        return cls.get(url, api_key).text

    @classmethod
    def read_json(cls, url, api_key):
        return json.loads(cls.read_url(url, api_key))


class AplusData(object):

    TIME_KEY = 'Time'
    USER_KEY = 'UserID'
    SUBMISSION_KEY = 'SubmissionID'
    GRADE_KEY = 'Grade'
    PENALTY_KEY = 'Penalty'
    REMOVE_KEYS = ['ExerciseID', 'Category', 'Exercise', 'StudentID', 'Email', 'Graded', 'GraderEmail', 'Notified', 'NSeen', '__grader_lang']

    def __init__(self, file_name):
        self.file_name = file_name

    def from_url_to_file(self, url, api_key):
        self.write(AplusQuery.read_url(url, api_key))
        self.read()

    def read(self):
        if os.path.isfile(self.file_name):
            self.data = pd.read_csv(self.file_name)
        else:
            self.data = pd.DataFrame({k: [] for k in [self.TIME_KEY, self.USER_KEY, self.SUBMISSION_KEY]})

    def write(self, text=None):
        dir = os.path.dirname(self.file_name)
        if not os.path.isdir(dir):
            os.mkdir(dir)
        with open(self.file_name, 'w') as fp:
            fp.write(self.data.to_csv(index=False) if text is None else text)

    def strip(self):
        strip_cols = [col for col in self.REMOVE_KEYS if col in self.data.columns]
        strip_cols.extend(col for col in self.data.columns if col.startswith('Unnamed: '))
        self.data = self.data.drop(columns=strip_cols).reset_index(drop=True)

    def parse_time(self):
        self.data[self.TIME_KEY] = pd.to_datetime(self.data[self.TIME_KEY])

    def strip_to_last_by_user(self):
        self.parse_time()
        user_time_map = {}
        for index, row in self.data.iterrows():
            if (
                not row[self.USER_KEY] in user_time_map
                or row[self.TIME_KEY] > user_time_map[row[self.USER_KEY]]['time']
            ):
                user_time_map[row[self.USER_KEY]] = {
                    'index': index,
                    'time': row[self.TIME_KEY]
                }
        rows = [entry['index'] for uid,entry in user_time_map.items()]
        self.data = self.data.iloc[rows, :].reset_index(drop=True)

    def cancel_penalty(self):
        def cancel_apply(row):
            if row[self.PENALTY_KEY] > 0:
                row[self.GRADE_KEY] /= row[self.PENALTY_KEY]
            return row
        if self.PENALTY_KEY in self.data:
            self.data = self.data.apply(cancel_apply, 1)
            self.data = self.data.drop(columns=[self.PENALTY_KEY]).reset_index(drop=True)

    def rows_having(self, key, value):
        return self.data[self.data[key] == value]

    def rows_not_having(self, key, value):
        return self.data[self.data[key] != value]

    def submission_rows(self):
        self.parse_time()
        return [(
            row[self.SUBMISSION_KEY] if self.SUBMISSION_KEY in row else None,
            row[self.USER_KEY],
            int(row[self.TIME_KEY].timestamp()),
            row
        ) for index, row in self.data.iterrows()]


class Consents(AplusData):

    def __init__(self, file_name, consent_key, yes_value):
        super().__init__(file_name)
        self.consent_key = consent_key
        self.yes_value = yes_value
        self.read()

    def rows_by_consent(self, yes_no=True):
        if yes_no:
            return self.rows_having(self.consent_key, self.yes_value)
        return self.rows_not_having(self.consent_key, self.yes_value)

    def strip_to_consent(self):
        self.data = self.rows_by_consent(True)

    def consent_user_ids(self):
        return self.rows_by_consent(True)[self.USER_KEY]

    def numbers(self):
        n = len(self.data)
        a = len(self.rows_by_consent(True))
        b = len(self.rows_by_consent(False))
        assert n == a + b
        return {
            'total': n,
            'consent': a,
            'decline': b,
            'ratio': a / n if n > 0 else 0.0
        }

    def anonymize(self, user_map, name, keys, url):
        print('Consents are not anonymized.')


class Exercise(AplusData):

    POINTS_KEY = 'Grade'
    PENALTY_KEY = 'Penalty'

    def __init__(self, file_name, max_points=0):
        super().__init__(file_name)
        self.max_points = max_points
        self.read()

    def strip_to_consent(self, consents, dir):
        select = self.data[self.USER_KEY].isin(consents.consent_user_ids())
        for index,row in self.data[~select].iterrows():
            dir.remove(row[self.USER_KEY])
        self.data = self.data[self.data[self.USER_KEY].isin(consents.consent_user_ids())]

    def numbers(self):
        return {
            'rows': len(self.data)
        }

    def count_and_best(self):
        agg = {}
        for index,row in self.data.iterrows():
            id = row[self.USER_KEY]
            points = float(row[self.POINTS_KEY] or 0)
            if self.PENALTY_KEY in row:
                penalty = float(row[self.PENALTY_KEY] or 0)
                if penalty > 0:
                    points /= penalty
            if self.max_points > 0:
                points /= self.max_points
            if id in agg:
                row = agg[id]
                row['count'] += 1
                if points > row['best']:
                    row.update({'best': points})
            else:
                agg[id] = {
                    'id': id,
                    'count': 1,
                    'best': points
                }
        return agg

    def anonymize(self, user_map, name, keys, url):
        self.parse_time()
        self.data = self.data.drop(columns=[self.SUBMISSION_KEY]).reset_index(drop=True)
        def user_map_apply(row):
            uid = row[self.USER_KEY]
            if not uid in user_map:
                raise RuntimeError('uid not in user_map from consents')
            new_uid = user_map.index(uid)
            row[self.USER_KEY] = new_uid
            for field in keys:
                if str(row[field]).startswith(url):
                    row[field] = os.path.join(name, str(new_uid), str(int(row[self.TIME_KEY].timestamp())), field)
            return row
        self.data = self.data.apply(user_map_apply, 1)


class DataDir(object):

    def __init__(self, base_dir):
        self.dir = base_dir
        self.mkdir(self.dir)

    def mkdir(self, dir):
        if not os.path.isdir(dir):
            os.mkdir(dir)

    def path(self, user_id, timestamp, file_name):
        return os.path.join(self.dir, str(user_id), str(timestamp), file_name)

    def exists(self, path):
        return os.path.exists(path)

    def remove(self, user_id):
        def rmr(path):
            if os.path.exists(path):
                for f in os.listdir(path):
                    p = os.path.join(path, f)
                    if os.path.isfile(p):
                        os.unlink(p)
                    else:
                        rmr(p)
                        os.rmdir(p)
        rmr(os.path.join(self.dir, str(user_id)))

    def get_encoding(self, path):
        from chardet import detect
        with open(path, 'rb') as f:
            rawdata = f.read()
            return detect(rawdata)['encoding']

    def read_text(self, path, encoding='utf-8'):
        with open(path, 'r', encoding=encoding, errors='replace') as fp:
            return fp.read()

    def read_lines(self, path):
        with open(path, 'r') as fp:
            return list(fp)

    def write(self, user_id, timestamp, file_name, content, binary=False):
        user_dir = os.path.join(self.dir, str(user_id))
        self.mkdir(user_dir)
        item_dir = os.path.join(user_dir, str(timestamp))
        self.mkdir(item_dir)
        with open(os.path.join(item_dir, file_name), 'wb' if binary else 'w') as fp:
            fp.write(content)

    def from_url_to_file(self, url, api_key, user_id, timestamp, file_name):
        if self.exists(self.path(user_id, timestamp, file_name)):
            print('Skip', url)
            return False
        self.write(user_id, timestamp, file_name, AplusQuery.read_url(url, api_key))
        return True

    def from_json_to_file(self, url, api_key, user_id, timestamp, file_name, field_key):
        if self.exists(self.path(user_id, timestamp, file_name)):
            print('Skip', url)
            return False
        data = AplusQuery.read_json(url, api_key)
        self.write(user_id, timestamp, file_name, json.dumps(data.get(field_key, {})))
        return True

    def from_file_to_file(self, url, api_key, user_id, timestamp, file_name):
        if self.exists(self.path(user_id, timestamp, file_name)):
            print('Skip', url)
            return False
        r = AplusQuery.get(url.split('?')[0], api_key)
        #cd = r.headers.get('Content-Disposition')
        #file_name = cd[22:-1] if cd and cd.startswith('attachment; filename="') else file_name_fallback
        self.write(user_id, timestamp, file_name, r.content, binary=True)
        return True

    def convert_to_utf8(self, user_id, timestamp, file_name):
        path = self.path(user_id, timestamp, file_name)
        if self.exists(path):
            encoding = self.get_encoding(path)
            if not encoding in ('utf-8', 'ascii'):
                self.write(user_id, timestamp, file_name, self.read_text(path, encoding))

    def strip_lines(self, user_id, timestamp, file_name, prefix):
        path = self.path(user_id, timestamp, file_name)
        if self.exists(path):
            lines = [l for l in self.read_lines(path) if not l.startswith(prefix)]
            self.write(user_id, timestamp, file_name, ''.join(lines))

    def anonymize(self, user_map):
        for i,uid in enumerate(user_map):
            path = os.path.join(self.dir, str(uid))
            if self.exists(path):
                os.rename(path, os.path.join(self.dir, str(i)))

    def try_unittest_fingerprint(self, user_id, timestamp):
        path = self.path(user_id, timestamp, 'test.txt')
        if self.exists(path):
            with open(path, 'r') as fp:
                return fp.readline()
        return None
