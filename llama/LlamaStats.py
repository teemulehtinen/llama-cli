import numpy
import pandas

from .common import (
  as_minute_scalar, df_adjust_index_to_zero, df_complete_n_index,
  df_sum, df_sum_by_index, df_index_sums, flatten_dict, groupby_as_ones,
  groupby_nth_deltas, measures, strip_outliers, sums_measures
)
from .operations import (
  WEEKDAY_KEY, WEEKNUMBER_KEY, HOUR_KEY,
  append_discrete_time_columns, times_until_end, times_nth_delta
)
from .plotting import limited_minute_bins, nice_bins, nice_plot_page
from .Config import TIME_KEY, PERSON_KEY, GRADE_KEY

COUNT_KEY = 'Count'
EXERCISE_KEY = 'Exercise'
GRADERATIO_KEY = 'Graderatio'
CHANGE_KEY = 'Change'
WDAYS = ['S','M','T','W','T','F','S']

class LlamaStats:

  @staticmethod
  def overall_series(table_iterator, rev_n=2):
    count = 0
    p_grades = pandas.DataFrame()
    p_actions = pandas.DataFrame()
    p_exercises = pandas.DataFrame()
    w_grades = pandas.DataFrame()
    w_count = pandas.DataFrame()
    wd_count = pandas.DataFrame()
    h_count = pandas.DataFrame()
    grade_ratios = pandas.Series()
    first_grades = pandas.Series()
    grade_changes = pandas.Series()
    exercise_actions = pandas.Series()
    exercise_persons = []
    end_minutes = pandas.Series()
    rev_minutes = [pandas.Series() for _ in range(rev_n)]
    rev_grades = [pandas.Series() for _ in range(rev_n)]
    rev_changes = [pandas.Series() for _ in range(rev_n)]
    for _, table, rows in table_iterator:
      append_discrete_time_columns(rows)
      rows[TIME_KEY] = as_minute_scalar(rows[TIME_KEY])
      mp = table.get('max_points', numpy.max(rows[GRADE_KEY]))
      rows[GRADERATIO_KEY] = rows[GRADE_KEY] / mp
      byperson = rows.groupby(PERSON_KEY)
      maxgrades = byperson[GRADE_KEY].max()
      count += 1
      p_grades = df_sum(p_grades, maxgrades)
      p_actions = df_sum(p_actions, byperson.size(), COUNT_KEY)
      p_exercises = df_sum(p_exercises, groupby_as_ones(byperson), COUNT_KEY)
      w_grades = df_sum_by_index(w_grades, maxgrades, byperson[WEEKNUMBER_KEY].median().astype('int'))
      w_count = df_sum(w_count, rows.groupby(WEEKNUMBER_KEY).size(), COUNT_KEY)
      wd_count = df_sum(wd_count, rows.groupby(WEEKDAY_KEY).size(), COUNT_KEY)
      h_count = df_sum(h_count, rows.groupby(HOUR_KEY).size(), COUNT_KEY)
      grade_ratios = grade_ratios.append(byperson[GRADERATIO_KEY].max(), True)
      first_grades = first_grades.append(byperson[GRADERATIO_KEY].first(), True)
      grade_changes = grade_changes.append(byperson[GRADERATIO_KEY].diff().dropna(), True)
      exercise_actions = exercise_actions.append(byperson.size(), True)
      exercise_persons.append(len(byperson))
      end_minutes = end_minutes.append(times_until_end(byperson), True)
      for i in range(rev_n):
        rev_minutes[i] = rev_minutes[i].append(times_nth_delta(byperson, i + 1), True)
        rev_grades[i] = rev_grades[i].append(byperson[GRADERATIO_KEY].nth(i + 1).dropna(), True)
        rev_changes[i] = rev_changes[i].append(groupby_nth_deltas(byperson, GRADERATIO_KEY, i + 1), True)
    week = df_adjust_index_to_zero(w_grades.join(w_count))
    return {
      '_values': {
        'table_count': count,
      },
      'learner_grades': p_grades[GRADE_KEY],
      'learner_actions': p_actions[COUNT_KEY],
      'learner_exercises': p_exercises[COUNT_KEY],
      'week_grade_sums': week[GRADE_KEY],
      'week_action_sums': week[COUNT_KEY],
      'weekly_action_sums': df_complete_n_index(wd_count, 7)[COUNT_KEY],
      'daily_action_sums': df_complete_n_index(h_count, 24)[COUNT_KEY],
      'grade_ratios': grade_ratios,
      'first_grades': first_grades,
      'grade_changes': grade_changes,
      'exercise_actions': exercise_actions,
      'exercise_persons': pandas.Series(exercise_persons),
      'end_minutes': end_minutes,
      **{f'revision_{i + 1}_minutes': rev_minutes[i] for i in range(rev_n)},
      **{f'revision_{i + 1}_grades': rev_grades[i] for i in range(rev_n)},
      **{f'revision_{i + 1}_changes': rev_changes[i] for i in range(rev_n)},
    }

  @staticmethod
  def overall_plot(ovseries):
    vals = ovseries['_values']
    minute_bins = limited_minute_bins(ovseries['end_minutes'])
    nice_plot_page(
      f'Overall statistics ({vals["table_count"]} tables)',
      [
        ('Learner grades', 'learner_grades'),
        ('Learner actions', 'learner_actions'),
        ('Learner exercises', 'learner_exercises'),
        ('Exercise grades', 'grade_ratios', {'range': nice_bins(0, 1)}),
        ('Exercise actions', 'exercise_actions'),
        ('Exercise end minutes', 'end_minutes', {'range': minute_bins}),
        ('Grade/Week', 'week_grade_sums'),
        ('Actions/Week', 'week_action_sums'),
        ('1st revision minutes', 'revision_1_minutes', {'range': minute_bins}),
        ('Weekly actions', 'weekly_action_sums', {'ticks': WDAYS}),
        ('Daily actions', 'daily_action_sums'),
        ('2nd revision minutes', 'revision_2_minutes', {'range': minute_bins}),
      ],
      ovseries
    )

  @staticmethod
  def learner_series(table_iterator, rev_n=2):
    count = 0
    learners = {}
    KEEP_KEYS = [GRADE_KEY, TIME_KEY, WEEKNUMBER_KEY, WEEKDAY_KEY, HOUR_KEY, EXERCISE_KEY, GRADERATIO_KEY]
    for _, table, rows in table_iterator:
      append_discrete_time_columns(rows)
      rows[TIME_KEY] = as_minute_scalar(rows[TIME_KEY])
      rows[EXERCISE_KEY] = [count for _ in range(rows.shape[0])]
      mp = table.get('max_points', numpy.max(rows[GRADE_KEY]))
      rows[GRADERATIO_KEY] = rows[GRADE_KEY] / mp
      for person, g_rows in rows.groupby(PERSON_KEY):
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
      w_count = rows.groupby(WEEKNUMBER_KEY).size().to_frame(COUNT_KEY)
      wd_count = rows.groupby(WEEKDAY_KEY).size().to_frame(COUNT_KEY)
      h_count = rows.groupby(HOUR_KEY).size().to_frame(COUNT_KEY)
      week = df_adjust_index_to_zero(w_grades.join(w_count))
      return {
        '_values': {
          'person': person,
          'grade_sum': int(numpy.sum(maxgrades)),
          'action_sum': int(numpy.sum(byexercise.size())),
          'exercise_sum': int(numpy.sum(groupby_as_ones(byexercise))),
        },
        'grade_ratios': byexercise[GRADERATIO_KEY].max(),
        'exercise_actions': byexercise.size(),
        'week_grade_sums': week[GRADE_KEY],
        'week_action_sums': week[COUNT_KEY],
        'weekly_action_sums': df_complete_n_index(wd_count, 7)[COUNT_KEY],
        'daily_action_sums': df_complete_n_index(h_count, 24)[COUNT_KEY],
        'end_minutes': times_until_end(byexercise),
        **{f'revision_{i}_minutes': times_nth_delta(byexercise, i) for i in range(1, rev_n + 1)},
      }
    return [person_dict(person, rows) for person, rows in learners.items()]

  @staticmethod
  def learner_plot(leseries, ovseries=None):
    vals = leseries['_values']
    minute_bins = limited_minute_bins(leseries['end_minutes'])
    nice_plot_page(
      f'Learner #{vals["person"]}',
      [
        (f'Grade: {vals["grade_sum"]}', 'learner_grades', {'show': vals['grade_sum']}),
        (f'Actions: {vals["action_sum"]}', 'learner_actions', {'show': vals['action_sum']}),
        (f'Exercises: {vals["exercise_sum"]}', 'learner_exercises', {'show': vals['exercise_sum']}),
        ('Exercise grades', 'grade_ratios', {'range': nice_bins(0, 1)}),
        ('Exercise actions', 'exercise_actions'),
        ('Exercise end minutes', 'end_minutes', {'range': minute_bins}),
        ('Grade/Week', 'week_grade_sums'),
        ('Actions/Week', 'week_action_sums'),
        ('1st revision minutes', 'revision_1_minutes', {'range': minute_bins}),
        ('Weekly actions', 'weekly_action_sums', {'ticks': WDAYS}),
        ('Daily actions', 'daily_action_sums'),
        ('2nd revision minutes', 'revision_2_minutes', {'range': minute_bins}),
      ],
      leseries,
      ovseries,
    )

  @classmethod
  def learner_variables(cls, leseries):
    return (
      leseries['_values']['person'],
      cls.variables(leseries, ['person', 'grade_sum', 'action_sum', 'exercise_sum'])
    )

  @staticmethod
  def exercise_series(table, rows, rev_n=2):
    append_discrete_time_columns(rows)
    rows[TIME_KEY] = as_minute_scalar(rows[TIME_KEY])
    mp = table.get('max_points', numpy.max(rows[GRADE_KEY]))
    rows[GRADERATIO_KEY] = rows[GRADE_KEY] / mp
    byperson = rows.groupby(PERSON_KEY)
    return {
      '_values': {
        'name': table['name'],
        'max_points': mp,
        'person_count': len(rows[PERSON_KEY].unique()),
      },
      'grade_ratios': byperson[GRADERATIO_KEY].max(),
      'exercise_actions': byperson.size(),
      'first_grades': byperson[GRADERATIO_KEY].first(),
      'grade_changes': byperson[GRADERATIO_KEY].diff().dropna(),
      'end_minutes': times_until_end(byperson),
      **{f'revision_{i}_minutes': times_nth_delta(byperson, i) for i in range(1, rev_n + 1)},
      **{f'revision_{i}_grades': byperson[GRADERATIO_KEY].nth(i).dropna() for i in range(1, rev_n + 1)},
      **{f'revision_{i}_changes': groupby_nth_deltas(byperson, GRADERATIO_KEY, i) for i in range(1, rev_n + 1)},
    }

  @staticmethod
  def exercise_plot(exseries, ovseries=None):
    vals = exseries['_values']
    grade_bins = nice_bins(0, 1)
    change_bins = nice_bins(-1, 1)
    minute_bins = limited_minute_bins(exseries['end_minutes'])
    nice_plot_page(
      vals['name'],
      [
        ('Best grades', 'grade_ratios', {'range': grade_bins}),
        ('Actions', 'exercise_actions'),
        (f'Learners: {vals["person_count"]}', 'exercise_persons', {'show': vals['person_count']}),
        ('First grades', 'first_grades', {'range': grade_bins}),
        ('Grade changes', 'grade_changes', {'range': change_bins}),
        ('End minutes', 'end_minutes', {'range': minute_bins}),
        ('1st revision grade', 'revision_1_grades', {'range': grade_bins}),
        ('1st revision changes', 'revision_1_changes', {'range': change_bins}),
        ('1st revision minutes', 'revision_1_minutes', {'range': minute_bins}),
        ('2nd revision grade', 'revision_2_grades', {'range': grade_bins}),
        ('2nd revision changes', 'revision_2_changes', {'range': change_bins}),
        ('2nd revision minutes', 'revision_2_minutes', {'range': minute_bins}),
      ],
      exseries,
      ovseries
    )

  @classmethod
  def exercise_variables(cls, exseries):
    return (
      exseries['_values']['name'],
      cls.variables(exseries, ['person_count'])
    )

  @staticmethod
  def description(series):
    return pandas.DataFrame({
      k: (strip_outliers(k, s) if k.endswith('_minutes') else s).describe()
      for k, s in series.items() if not k.startswith('_')
    })

  @staticmethod
  def variables(series, values_keys):
    def extract(k, s):
      if k.endswith('_sum'):
        ms = sums_measures(s)
      else:
        ms = measures(s[s <= 20] if k.endswith('minutes') else s)
      return {'md': ms['m'], 'mad': ms['mad']}
    return {
      **{k: series['_values'][k] for k in values_keys},
      **flatten_dict({ k: extract(k, s) for k, s in series.items() if k != '_values'}),
    }
