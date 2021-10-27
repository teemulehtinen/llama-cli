import numpy
import pandas
from scipy import stats
from matplotlib import pyplot
from .Config import TIME_KEY, PERSON_KEY, GRADE_KEY
from .plotting import nice_hist

class LlamaStats:

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

  @staticmethod
  def nth_delta(series, n=1):
    if series.shape[0] > n:
      return series.values[n] - series.values[n - 1]
    else:
      return numpy.nan

  @staticmethod
  def minutescalar(data):
    return data.astype('int64') // 1e9 / 60

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

  @classmethod
  def exercise_description(cls, exseries):
    return pandas.DataFrame({
      k: (cls.strip_outliers(k, s) if k.endswith('_minutes') else s).describe()
      for k, s in exseries.items() if not k.startswith('_')
    })

  @staticmethod
  def exercise_plot(table, exseries):
    _, ax = pyplot.subplots(4, 3, figsize=(7, 10), gridspec_kw={ 'hspace': 0.4, 'wspace': 0.3 })
    pyplot.suptitle(table['name'])
    mp = table['max_points'] if 'max_points' in table else numpy.max(exseries['best_grades'])
    grade_step = mp / 10
    grade_bins = numpy.arange(0, mp + 2 * grade_step, grade_step)
    nice_hist(ax[0, 0], '1st grade', exseries['first_grades'], grade_bins)
    nice_hist(ax[1, 0], '2nd grade', exseries['revision_1_grades'], grade_bins)
    nice_hist(ax[2, 0], '3rd grade', exseries['revision_2_grades'], grade_bins)
    nice_hist(ax[3, 0], 'Best grade', exseries['best_grades'], grade_bins)
    ms = numpy.max(exseries['attempts'])
    mm = max(numpy.quantile(exseries['end_minutes'], 0.7), 10)
    minute_bins = numpy.arange(0, mm, mm / 10)
    nice_hist(ax[0, 1], 'Attempts', exseries['attempts'], numpy.arange(1, ms + 2, 1))
    nice_hist(ax[1, 1], '2nd minutes', exseries['revision_1_minutes'], minute_bins)
    nice_hist(ax[2, 1], '3rd minutes', exseries['revision_2_minutes'], minute_bins)
    nice_hist(ax[3, 1], 'End minutes', exseries['end_minutes'], minute_bins)
    change_step = 2 * grade_step
    change_bins = numpy.arange(-mp, mp + 2 * change_step, change_step)
    nice_hist(ax[0, 2], 'Every grading', exseries['every_grading'], grade_bins)
    nice_hist(ax[1, 2], '2nd changes', exseries['revision_1_changes'], change_bins)
    nice_hist(ax[2, 2], '3rd changes', exseries['revision_2_changes'], change_bins)
    nice_hist(ax[3, 2], 'All changes', exseries['grade_changes'], change_bins)
