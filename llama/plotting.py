import numpy
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import FuncFormatter

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

def nice_bins(min, max, steps=10):
  s = (max - min) / steps
  return numpy.arange(min, max + 2 * s, s)

def limited_minute_bins(series, quantile=0.6, min=10):
  return nice_bins(0, max(numpy.quantile(series, quantile), min))

def nice_formatter(x, pos):
  if x > 1000000:
    return f'{int(x // 1000000)}M'
  if x > 1000:
    return f'{int(x // 1000)}K'
  return int(x)

def nice_hist(axis, title, series, bins=None, color=None):
  axis.set_title(title)
  nb = bins if not bins is None else nice_bins(numpy.min(series), numpy.max(series))
  n, _, _ = axis.hist(series, nb, color=color)
  cx = (nb[0] + nb[-1]) / 2
  txt = f'N = {series.shape[0]}'
  if numpy.sum(n) > 0:
    t = numpy.max(n)
    if t >= 1000:
      axis.yaxis.set_major_formatter(FuncFormatter(nice_formatter))
    axis.text(cx, 0.9 * t, txt, ha='center', va='center')
  else:
    axis.set_ylim(0, 1)
    axis.text(cx, 0.9, txt, ha='center', va='center')

def nice_bars(axis, title, series, ticks=None):
  axis.set_title(title)
  axis.bar(series.index, series, 1, tick_label=ticks)
  if numpy.max(series) >= 1000:
    axis.yaxis.set_major_formatter(FuncFormatter(nice_formatter))
