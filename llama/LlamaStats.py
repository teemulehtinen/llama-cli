import numpy
import pandas
from scipy import stats
from matplotlib import pyplot
from .Config import TIME_KEY, PERSON_KEY, GRADE_KEY
from .plotting import nice_bars, nice_bins, nice_hist

ATTEMPT_KEY = 'Attempt'
WEEKDAY_KEY = 'Weekday'
WEEKNUMBER_KEY = 'Weeknumber'
EXERCISE_KEY = 'Exercise'
GRADERATIO_KEY = 'Graderatio'
WDAYS = ['S','M','T','W','T','F','S']

class LlamaStats:

  @classmethod
  def overall_series(cls, table_iterator):
    count = 0
    p_grades = pandas.DataFrame()
    p_attempts = pandas.DataFrame()
    wd_grades = pandas.DataFrame()
    wd_attempts = pandas.DataFrame()
    w_grades = pandas.DataFrame()
    w_attempts = pandas.DataFrame()
    for _, _, rows in table_iterator:
      cls.calculate_discrete_time_columns(rows)
      byperson = rows.groupby(PERSON_KEY)
      maxgrades = byperson[GRADE_KEY].max()
      count += 1
      p_grades = cls.df_sum(p_grades, GRADE_KEY, maxgrades)
      p_attempts = cls.df_sum(p_attempts, ATTEMPT_KEY, byperson.size())
      wd_grades = cls.df_sum_by_index(wd_grades, GRADE_KEY, maxgrades, byperson[WEEKDAY_KEY].median().astype('int'))
      wd_attempts = cls.df_sum(wd_attempts, ATTEMPT_KEY, rows.groupby(WEEKDAY_KEY).size())
      w_grades = cls.df_sum_by_index(w_grades, GRADE_KEY, maxgrades, byperson[WEEKNUMBER_KEY].median().astype('int'))
      w_attempts = cls.df_sum(w_attempts, ATTEMPT_KEY, rows.groupby(WEEKNUMBER_KEY).size())
    w_grades, w_attempts = cls.number_weeks_from_zero(w_grades, w_attempts)
    return {
      '_table_count': count,
      'person_grades': p_grades[GRADE_KEY],
      'person_attempts': p_attempts[ATTEMPT_KEY],
      '_weekday': cls.ensure_weekday_index(wd_grades.join(wd_attempts)),
      '_weekcount': w_grades.join(w_attempts),
    }

  @staticmethod
  def overall_plot(ovseries):
    _, ax = pyplot.subplots(3, 2, figsize=(7, 10), gridspec_kw={ 'hspace': 0.4, 'wspace': 0.3 })
    pyplot.suptitle(f'Overall statistics ({ovseries["_table_count"]} tables)')
    nice_hist(ax[0, 0], 'Grades', ovseries['person_grades'])
    nice_hist(ax[0, 1], 'Attempts', ovseries['person_attempts'])
    nice_bars(ax[1, 0], 'Grade/Week', ovseries['_weekcount'][GRADE_KEY])
    nice_bars(ax[1, 1], 'Attempts/Week', ovseries['_weekcount'][ATTEMPT_KEY])
    nice_bars(ax[2, 0], 'Grade/Weekday', ovseries['_weekday'][GRADE_KEY], WDAYS)
    nice_bars(ax[2, 1], 'Attempts/Weekday', ovseries['_weekday'][ATTEMPT_KEY], WDAYS)

  @classmethod
  def learner_series(cls, table_iterator, include_persons=None):
    count = 0
    learners = {}
    KEEP_KEYS = [GRADE_KEY, WEEKDAY_KEY, WEEKNUMBER_KEY, EXERCISE_KEY, GRADERATIO_KEY]
    for _, table, rows in table_iterator:
      cls.calculate_discrete_time_columns(rows)
      rows[EXERCISE_KEY] = [count for i in range(rows.shape[0])]
      mp = table['max_points'] if 'max_points' in table else numpy.max(rows[GRADE_KEY])
      rows[GRADERATIO_KEY] = rows[GRADE_KEY] / mp
      for person, g_rows in rows.groupby(PERSON_KEY):
        if include_persons is None or person in include_persons:
          g_rows = g_rows.drop(columns=[c for c in g_rows.columns if not c in KEEP_KEYS]).reset_index(drop=True)
          if not person in learners:
            learners[person] = g_rows
          else:
            learners[person] = learners[person].append(g_rows, ignore_index=True)
      count += 1
    def person_dict(person, rows):
      byexercise = rows.groupby(EXERCISE_KEY)
      maxgrades = byexercise[GRADE_KEY].max()
      wd_grades = cls.sum_by_index(maxgrades, GRADE_KEY, byexercise[WEEKDAY_KEY].median().astype('int'))
      wd_attempts = rows.groupby(WEEKDAY_KEY).size().to_frame(ATTEMPT_KEY)
      w_grades = cls.sum_by_index(maxgrades, GRADE_KEY, byexercise[WEEKNUMBER_KEY].median().astype('int'))
      w_attempts = rows.groupby(WEEKNUMBER_KEY).size().to_frame(ATTEMPT_KEY)
      w_grades, w_attempts = cls.number_weeks_from_zero(w_grades, w_attempts)
      return {
        '_person': person,
        'exercise_grades': maxgrades,
        'exercise_graderatios': byexercise[GRADERATIO_KEY].max(),
        'exercise_attempts': byexercise.size(),
        '_weekday': cls.ensure_weekday_index(wd_grades.join(wd_attempts)),
        '_weekcount': w_grades.join(w_attempts),
      }
    return [person_dict(person, rows) for person, rows in learners.items()]

  @staticmethod
  def learner_plot(leseries):
    _, ax = pyplot.subplots(4, 2, figsize=(7, 10), gridspec_kw={ 'hspace': 0.4, 'wspace': 0.3 })
    pyplot.suptitle(f'Learner #{int(leseries["_person"])}')
    nice_hist(ax[0, 0], 'Grades', leseries['exercise_graderatios'])
    nice_hist(ax[0, 1], 'Attempts', leseries['exercise_attempts'])
    nice_bars(ax[1, 0], 'Grade/exercise', leseries['exercise_grades'])
    nice_bars(ax[1, 1], 'Attempts/exercise', leseries['exercise_attempts'])
    nice_bars(ax[2, 0], 'Grade/week', leseries['_weekcount'][GRADE_KEY])
    nice_bars(ax[2, 1], 'Attempts/week', leseries['_weekcount'][ATTEMPT_KEY])
    nice_bars(ax[3, 0], 'Grade/weekday', leseries['_weekday'][GRADE_KEY], WDAYS)
    nice_bars(ax[3, 1], 'Attempts/weekday', leseries['_weekday'][ATTEMPT_KEY], WDAYS)

  @classmethod
  def exercise_series(cls, rows, rev_n=2):
    rows[TIME_KEY] = cls.minutescalar(rows[TIME_KEY])
    byperson = rows.groupby(PERSON_KEY)
    series = {
      '_person_count': len(rows[PERSON_KEY].unique()),
      'best_grades': byperson[GRADE_KEY].max(),
      'first_grades': byperson[GRADE_KEY].first(),
      'every_grading': rows[GRADE_KEY],
      'attempts': byperson.size(),
      'end_minutes': byperson[TIME_KEY].max() - byperson[TIME_KEY].min(),
      'grade_changes': byperson[GRADE_KEY].diff().dropna(),
    }
    for i in range(1, rev_n + 1):
      rev_t = byperson[TIME_KEY].apply(cls.nth_delta, n=i).to_frame(TIME_KEY)
      rev_c = byperson[GRADE_KEY].apply(cls.nth_delta, n=i).to_frame('Change')
      rev_g = byperson[GRADE_KEY].nth(i).to_frame(GRADE_KEY)
      rev = rev_t.join([rev_c, rev_g]).dropna()
      series[f'revision_{i}_minutes'] = rev[TIME_KEY]
      series[f'revision_{i}_changes'] = rev['Change']
      series[f'revision_{i}_grades'] = rev[GRADE_KEY]
    return series

  @staticmethod
  def exercise_plot(table, exseries):
    _, ax = pyplot.subplots(4, 3, figsize=(7, 10), gridspec_kw={ 'hspace': 0.4, 'wspace': 0.3 })
    pyplot.suptitle(table['name'])
    mp = table['max_points'] if 'max_points' in table else numpy.max(exseries['best_grades'])
    grade_bins = nice_bins(0, mp)
    nice_hist(ax[0, 0], '1st grade', exseries['first_grades'], grade_bins)
    nice_hist(ax[1, 0], '2nd grade', exseries['revision_1_grades'], grade_bins)
    nice_hist(ax[2, 0], '3rd grade', exseries['revision_2_grades'], grade_bins)
    nice_hist(ax[3, 0], 'Best grade', exseries['best_grades'], grade_bins)
    mm = max(numpy.quantile(exseries['end_minutes'], 0.7), 10)
    minute_bins = nice_bins(0, mm)
    nice_hist(ax[0, 1], 'Every grading', exseries['every_grading'], grade_bins)
    nice_hist(ax[1, 1], '2nd minutes', exseries['revision_1_minutes'], minute_bins)
    nice_hist(ax[2, 1], '3rd minutes', exseries['revision_2_minutes'], minute_bins)
    nice_hist(ax[3, 1], 'End minutes', exseries['end_minutes'], minute_bins)
    change_bins = nice_bins(-mp, mp)
    nice_hist(ax[0, 2], 'Attempts', exseries['attempts'])
    nice_hist(ax[1, 2], '2nd changes', exseries['revision_1_changes'], change_bins)
    nice_hist(ax[2, 2], '3rd changes', exseries['revision_2_changes'], change_bins)
    nice_hist(ax[3, 2], 'All changes', exseries['grade_changes'], change_bins)

  @classmethod
  def description(cls, exseries):
    return pandas.DataFrame({
      k: (cls.strip_outliers(k, s) if k.endswith('_minutes') else s).describe()
      for k, s in exseries.items() if not k.startswith('_')
    })

  @staticmethod
  def calculate_discrete_time_columns(rows):
    rows[WEEKDAY_KEY] = rows[TIME_KEY].dt.dayofweek
    rows[WEEKNUMBER_KEY] = rows[TIME_KEY].dt.weekofyear
  
  @classmethod
  def ensure_weekday_index(cls, df):
    zeros = [0 for i in range(7)]
    wd_zero = pandas.DataFrame({GRADE_KEY: zeros, ATTEMPT_KEY: zeros}, index=[i for i in range(7)])
    return df.add(wd_zero, fill_value=0)

  @classmethod
  def number_weeks_from_zero(cls, *dfs):
    w_start = min(numpy.min(t.index) for t in dfs)
    return [cls.df_adjust_index(t, 'Weekcount', -w_start) for t in dfs]

  @staticmethod
  def df_adjust_index(df, name, add):
    df[name] = df.index + add
    return df.set_index(name)

  @staticmethod
  def df_sum(to, key, series):
    return to.add(series.to_frame(key), fill_value=0)

  @classmethod
  def df_sum_by_index(cls, to, key, series, index):
    return to.add(cls.sum_by_index(series, key, index), fill_value=0)

  @staticmethod
  def sum_by_index(series, key, index):
    return series.to_frame(key).join(index).groupby(index.name).sum()

  @staticmethod
  def nth_delta(series, n=1):
    if series.shape[0] > n:
      return series.values[n] - series.values[n - 1]
    else:
      return numpy.nan

  @staticmethod
  def minutescalar(data):
    return data.astype('int64') // 1e9 / 60

  @staticmethod
  def split_outliers(series, max_z_score=2.5):
    if series.empty:
      return series, pandas.Series()
    accept = numpy.abs(stats.zscore(series)) < max_z_score
    return series[accept], series[~accept]
  
  @classmethod
  def strip_outliers(cls, key, series, max_z_score=2.5):
    accept, strip = cls.split_outliers(series, max_z_score)
    if not strip.empty:
      print(f'Stripped outliers for "{key}"', strip.to_numpy())
    return accept
