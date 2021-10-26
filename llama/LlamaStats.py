import pandas
import numpy
from scipy import stats
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages
from .Config import TIME_KEY, PERSON_KEY, GRADE_KEY

class LlamaStats:

  @staticmethod
  def remove_outliers(series, max_z_score=3):
    if series.empty:
      return series, pandas.Series()
    accept = numpy.abs(stats.zscore(series)) < max_z_score
    return series[accept], series[~accept]
  
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
  def exercise_series(cls, rows, rev_n=3):
    rows[TIME_KEY] = cls.minutescalar(rows[TIME_KEY])
    byperson = rows.groupby(PERSON_KEY)
    end_time, ol = cls.remove_outliers(
      byperson[TIME_KEY].max() - byperson[TIME_KEY].min()
    )
    if not ol.empty:
      print('Removed start-to-end outliers:', ol.to_numpy())
    revisions = []
    for i in range(1, rev_n + 1):
      rev_t, ol = cls.remove_outliers(
        byperson[TIME_KEY].apply(cls.nth_delta, n=i).dropna()
      )
      if not ol.empty:
        print('Removed revision time outliers:', ol.to_numpy())
      rev_t = rev_t.to_frame(TIME_KEY)
      rev_g = byperson[GRADE_KEY].nth(i).to_frame(GRADE_KEY)
      revisions.append(rev_t.join(rev_g).dropna())
    series = {
      'best_grade': byperson[GRADE_KEY].max(),
      'first_grade': byperson[GRADE_KEY].first(),
      'every_grading': rows[GRADE_KEY],
      'attempts': byperson.size(),
      'minutes_to_end': end_time,
      'grade_changes': byperson[GRADE_KEY].diff().dropna(),
    }
    for i, rev in enumerate(revisions):
      series[f'revision_{i + 1}_minutes'] = rev[TIME_KEY]
      series[f'revision_{i + 1}_grades'] = rev[GRADE_KEY]
    return series

  @staticmethod
  def exercise_description(series):
    return pandas.DataFrame({ k: s.describe() for k, s in series.items() })

  @staticmethod
  def exercise_plot(table, series):
    _, ax = pyplot.subplots(3, 3, figsize=(7, 10), gridspec_kw={ 'hspace': 0.3, 'wspace': 0.3 })
    pyplot.suptitle(table['name'])
    mp = table['max_points']
    grade_step = mp / 10
    grade_bins = numpy.arange(0, mp + 2 * grade_step, grade_step) - 0.5 * grade_step
    ax[0, 0].set_title('Best grade')
    ax[0, 0].hist(series['best_grade'], grade_bins)
    ax[0, 1].set_title('First grade')
    ax[0, 1].hist(series['first_grade'], grade_bins)
    ax[0, 2].set_title('Every grading')
    ax[0, 2].hist(series['every_grading'], grade_bins)
    ax[1, 0].set_title('Attempts (revisions)')
    ax[1, 0].hist(series['attempts'])
    ax[1, 1].set_title('Minutes until last')
    ax[1, 1].hist(series['minutes_to_end'])
    change_step = 2 * grade_step
    change_bins = numpy.arange(-mp - change_step, mp + change_step, change_step)
    ax[1, 2].set_title('Grade changes')
    ax[1, 2].hist(series['grade_changes'], change_bins)
    rev_titles = ('1st revision', '2nd revision', '3rd revision')
    for i in range(3):
      ax[2, i].set_title(rev_titles[i])
      ax[2, i].hist2d(
        series[f'revision_{i + 1}_minutes'],
        series[f'revision_{i + 1}_grades'],
        range=[[0, 120], [0, mp + grade_step]],
        cmap=pyplot.cm.Blues
      )
      ax[2, i].set_xlabel('Minutes')
      if i == 0:
        ax[2, i].set_ylabel('Grade')

  @staticmethod
  def multipage_plot_or_show(pdf_name, iterator, plot_function):
    if pdf_name:
      with PdfPages(pdf_name) as pdf:
        for r in iterator:
          plot_function(r)
          pdf.savefig()
    else:
      for r in iterator:
        plot_function(r)
        pyplot.show()
