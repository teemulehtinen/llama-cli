import pandas
import numpy
from scipy import stats
from matplotlib import pyplot
from .Config import TIME_KEY, PERSON_KEY, GRADE_KEY

class LlamaStats:

  @staticmethod
  def remove_outliers(series, max_z_score=3):
    accept = numpy.abs(stats.zscore(series)) < max_z_score
    return series[accept], series[~accept]

  @staticmethod
  def exercise_series(rows):
    byperson = rows.groupby(PERSON_KEY)
    changes = byperson[GRADE_KEY].diff()
    #rev_time = byperson[TIME_KEY].diff().astype('timedelta64[m]')
    #rev_time = rev_time[(rev_time > 0) & (rev_time < 3 * 60)]
    #timed = pandas.DataFrame(changes).join(rev_time).dropna()
    end_time, ol = LlamaStats.remove_outliers(
      (byperson[TIME_KEY].max() - byperson[TIME_KEY].min()).astype('timedelta64[m]')
    )
    if not ol.empty:
      print('Removed start-to-end outliers:', ol.to_numpy())
    return {
      'best_grade': byperson[GRADE_KEY].max(),
      'first_grade': byperson[GRADE_KEY].first(),
      'every_grading': rows[GRADE_KEY],
      'attempts': byperson.size(),
      'start_to_end_minutes': end_time,
      'grade_changes': changes,
      #TODO first revision: time, grade change
      #TODO second revision
      #TODO third revision
      #'revision_minutes': rev_time,
      #'grade_per_minute': timed[GRADE_KEY] / timed[TIME_KEY],
    }

  @staticmethod
  def exercise_description(series):
    return pandas.DataFrame({ k: s.describe() for k, s in series.items() })

  @staticmethod
  def exercise_plot(exercise_name, series):
    pandas.DataFrame(series).hist()
    pyplot.suptitle(exercise_name)
    pyplot.show()
