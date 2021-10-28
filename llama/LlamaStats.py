import numpy
import pandas
from matplotlib import pyplot
from .Config import TIME_KEY, PERSON_KEY, GRADE_KEY
from .common import (
  as_minute_scalar, df_adjust_index_to_zero, df_complete_n_index,
  df_sum, df_sum_by_index, df_index_sums, groupby_as_ones, nth_delta
)
from .operations import (
  WEEKDAY_KEY, WEEKNUMBER_KEY, HOUR_KEY, append_discrete_time_columns, times_until_end, times_until_rev
)
from .plotting import limited_minute_bins, nice_bars, nice_bins, nice_hist

ATTEMPT_KEY = 'Attempt'
EXERCISE_KEY = 'Exercise'
GRADERATIO_KEY = 'Graderatio'
WDAYS = ['S','M','T','W','T','F','S']

class LlamaStats:

  @staticmethod
  def overall_series(table_iterator):
    count = 0
    p_grades = pandas.DataFrame()
    p_attempts = pandas.DataFrame()
    p_exercises = pandas.DataFrame()
    w_grades = pandas.DataFrame()
    w_attempts = pandas.DataFrame()
    wd_grades = pandas.DataFrame()
    wd_attempts = pandas.DataFrame()
    h_grades = pandas.DataFrame()
    h_attempts = pandas.DataFrame()
    grade_ratios = pandas.Series()
    end_minutes = pandas.Series()
    first_minutes = pandas.Series()
    for _, table, rows in table_iterator:
      append_discrete_time_columns(rows)
      rows[TIME_KEY] = as_minute_scalar(rows[TIME_KEY])
      mp = table['max_points'] if 'max_points' in table else numpy.max(rows[GRADE_KEY])
      rows[GRADERATIO_KEY] = rows[GRADE_KEY] / mp
      byperson = rows.groupby(PERSON_KEY)
      maxgrades = byperson[GRADE_KEY].max()
      count += 1
      p_grades = df_sum(p_grades, maxgrades)
      p_attempts = df_sum(p_attempts, byperson.size(), ATTEMPT_KEY)
      p_exercises = df_sum(p_exercises, groupby_as_ones(byperson), ATTEMPT_KEY)
      w_grades = df_sum_by_index(w_grades, maxgrades, byperson[WEEKNUMBER_KEY].median().astype('int'))
      w_attempts = df_sum(w_attempts, rows.groupby(WEEKNUMBER_KEY).size(), ATTEMPT_KEY)
      wd_grades = df_sum_by_index(wd_grades, maxgrades, byperson[WEEKDAY_KEY].median().astype('int'))
      wd_attempts = df_sum(wd_attempts, rows.groupby(WEEKDAY_KEY).size(), ATTEMPT_KEY)
      h_grades = df_sum_by_index(h_grades, maxgrades, byperson[HOUR_KEY].median().astype('int'))
      h_attempts = df_sum(h_attempts, rows.groupby(HOUR_KEY).size(), ATTEMPT_KEY)
      grade_ratios = grade_ratios.append(byperson[GRADERATIO_KEY].max(), True)
      end_minutes = end_minutes.append(times_until_end(byperson), True)
      first_minutes = first_minutes.append(times_until_rev(byperson, 1), True)
    return {
      '_table_count': count,
      'person_grades': p_grades[GRADE_KEY],
      'person_attempts': p_attempts[ATTEMPT_KEY],
      'person_exercises': p_exercises[ATTEMPT_KEY],
      '_weekcount': df_adjust_index_to_zero(w_grades.join(w_attempts)),
      '_weekday': df_complete_n_index(wd_grades.join(wd_attempts), 7),
      '_hour': df_complete_n_index(h_grades.join(h_attempts), 24),
      'grade_ratios': grade_ratios,
      'end_minutes': end_minutes,
      'first_minutes': first_minutes,
    }

  @staticmethod
  def overall_plot(ovseries):
    _, ax = pyplot.subplots(4, 3, figsize=(7, 10), gridspec_kw={ 'hspace': 0.4, 'wspace': 0.3 })
    pyplot.suptitle(f'Overall statistics ({ovseries["_table_count"]} tables)')
    nice_hist(ax[0, 0], 'Learner grades', ovseries['person_grades'])
    nice_hist(ax[0, 1], 'Learner attempts', ovseries['person_attempts'])
    nice_hist(ax[0, 2], 'Learner exercises', ovseries['person_exercises'])
    nice_bars(ax[1, 0], 'Grade/Week', ovseries['_weekcount'][GRADE_KEY])
    nice_bars(ax[1, 1], 'Attempts/Week', ovseries['_weekcount'][ATTEMPT_KEY])
    nice_hist(ax[1, 2], 'Exercise grades', ovseries['grade_ratios'])
    minute_bins = limited_minute_bins(ovseries['end_minutes'])
    nice_bars(ax[2, 0], 'Grade/Weekday', ovseries['_weekday'][GRADE_KEY], WDAYS)
    nice_bars(ax[2, 1], 'Attempts/Weekday', ovseries['_weekday'][ATTEMPT_KEY], WDAYS)
    nice_hist(ax[2, 2], '1st revision minutes', ovseries['first_minutes'], minute_bins)
    nice_bars(ax[3, 0], 'Grade/Hour', ovseries['_hour'][GRADE_KEY])
    nice_bars(ax[3, 1], 'Attempts/Hour', ovseries['_hour'][ATTEMPT_KEY])
    nice_hist(ax[3, 2], 'Exercise end minutes', ovseries['end_minutes'], minute_bins)

  @staticmethod
  def learner_series(table_iterator, include_persons=None):
    count = 0
    learners = {}
    KEEP_KEYS = [GRADE_KEY, WEEKDAY_KEY, WEEKNUMBER_KEY, EXERCISE_KEY, GRADERATIO_KEY]
    for _, table, rows in table_iterator:
      append_discrete_time_columns(rows)
      rows[EXERCISE_KEY] = [count for i in range(rows.shape[0])]
      mp = table['max_points'] if 'max_points' in table else numpy.max(rows[GRADE_KEY])
      rows[GRADERATIO_KEY] = rows[GRADE_KEY] / mp
      for person, g_rows in rows.groupby(PERSON_KEY):
        if include_persons is None or person in include_persons:
          g_rows = g_rows.drop(columns=[c for c in g_rows.columns if not c in KEEP_KEYS])
          if not person in learners:
            learners[person] = g_rows.reset_index(drop=True)
          else:
            learners[person] = learners[person].append(g_rows, True)
      count += 1
    def person_dict(person, rows):
      byexercise = rows.groupby(EXERCISE_KEY)
      maxgrades = byexercise[GRADE_KEY].max()
      w_grades = df_index_sums(maxgrades, byexercise[WEEKNUMBER_KEY].median().astype('int'))
      w_attempts = rows.groupby(WEEKNUMBER_KEY).size().to_frame(ATTEMPT_KEY)
      wd_grades = df_index_sums(maxgrades, byexercise[WEEKDAY_KEY].median().astype('int'))
      wd_attempts = rows.groupby(WEEKDAY_KEY).size().to_frame(ATTEMPT_KEY)
      return {
        '_person': person,
        'exercise_grades': maxgrades,
        'exercise_grade_ratios': byexercise[GRADERATIO_KEY].max(),
        'exercise_attempts': byexercise.size(),
        '_weekcount': df_adjust_index_to_zero(w_grades.join(w_attempts)),
        '_weekday': df_complete_n_index(wd_grades.join(wd_attempts), 7),
      }
    return [person_dict(person, rows) for person, rows in learners.items()]

  @staticmethod
  def learner_plot(leseries):
    _, ax = pyplot.subplots(4, 2, figsize=(7, 10), gridspec_kw={ 'hspace': 0.4, 'wspace': 0.3 })
    pyplot.suptitle(f'Learner #{int(leseries["_person"])}')
    nice_hist(ax[0, 0], 'Grades', leseries['exercise_grade_ratios'])
    nice_hist(ax[0, 1], 'Attempts', leseries['exercise_attempts'])
    nice_bars(ax[1, 0], 'Grade/Exercise', leseries['exercise_grades'])
    nice_bars(ax[1, 1], 'Attempts/Exercise', leseries['exercise_attempts'])
    nice_bars(ax[2, 0], 'Grade/Week', leseries['_weekcount'][GRADE_KEY])
    nice_bars(ax[2, 1], 'Attempts/Week', leseries['_weekcount'][ATTEMPT_KEY])
    nice_bars(ax[3, 0], 'Grade/Weekday', leseries['_weekday'][GRADE_KEY], WDAYS)
    nice_bars(ax[3, 1], 'Attempts/Weekday', leseries['_weekday'][ATTEMPT_KEY], WDAYS)

  @staticmethod
  def exercise_series(rows, rev_n=2):
    rows[TIME_KEY] = as_minute_scalar(rows[TIME_KEY])
    byperson = rows.groupby(PERSON_KEY)
    series = {
      '_person_count': len(rows[PERSON_KEY].unique()),
      'best_grades': byperson[GRADE_KEY].max(),
      'first_grades': byperson[GRADE_KEY].first(),
      'every_grading': rows[GRADE_KEY],
      'attempts': byperson.size(),
      'end_minutes': times_until_end(byperson),
      'grade_changes': byperson[GRADE_KEY].diff().dropna(),
    }
    CHANGE_KEY = 'Change'
    for i in range(1, rev_n + 1):
      rev_t = byperson[TIME_KEY].apply(nth_delta, n=i).to_frame(TIME_KEY)
      rev_c = byperson[GRADE_KEY].apply(nth_delta, n=i).to_frame(CHANGE_KEY)
      rev_g = byperson[GRADE_KEY].nth(i).to_frame(GRADE_KEY)
      rev = rev_t.join([rev_c, rev_g]).dropna()
      series[f'revision_{i}_minutes'] = rev[TIME_KEY]
      series[f'revision_{i}_changes'] = rev[CHANGE_KEY]
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
    change_bins = nice_bins(-mp, mp)
    nice_hist(ax[0, 1], 'Every grading', exseries['every_grading'], grade_bins)
    nice_hist(ax[1, 1], '2nd changes', exseries['revision_1_changes'], change_bins)
    nice_hist(ax[2, 1], '3rd changes', exseries['revision_2_changes'], change_bins)
    nice_hist(ax[3, 1], 'All changes', exseries['grade_changes'], change_bins)
    minute_bins = limited_minute_bins(exseries['end_minutes'])
    nice_hist(ax[0, 2], 'Attempts', exseries['attempts'])
    nice_hist(ax[1, 2], '2nd minutes', exseries['revision_1_minutes'], minute_bins)
    nice_hist(ax[2, 2], '3rd minutes', exseries['revision_2_minutes'], minute_bins)
    nice_hist(ax[3, 2], 'End minutes', exseries['end_minutes'], minute_bins)

  @classmethod
  def description(cls, exseries):
    return pandas.DataFrame({
      k: (cls.strip_outliers(k, s) if k.endswith('_minutes') else s).describe()
      for k, s in exseries.items() if not k.startswith('_')
    })
