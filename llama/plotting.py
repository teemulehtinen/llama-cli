import math
import numpy
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import FuncFormatter
from .common import measures, sums_measures

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

def select_bin(v, bins):
  try:
    i = next(i for i, w in enumerate(bins) if v < w)
    if i > 0:
      return i - 1
  except StopIteration:
    pass
  return None

def nf(x, pos=None):
  if numpy.isnan(x):
    return x
  if abs(x) > 1000000:
    return f'{int(x // 1000000)}M'
  if abs(x) > 1000:
    return f'{int(x // 1000)}K'
  if abs(x) < 10 and x % 1 != 0:
    return round(x, 1)
  return int(x)

def nice_title(desc, mes, cmp):
  lines = [
    desc,
    f'N={nf(mes["n"])} {mes["label"]}={nf(mes["m"])} MAD={nf(mes["mad"])}'
  ]
  if not cmp is None:
    dm = mes['m'] - cmp['m']
    dmad = mes['mad'] - cmp['mad']
    lines.append(f'(cf. {mes["label"]} {nf(dm)} MAD {nf(dmad)})')
  return '\n'.join(lines)

def nice_hist(axis, title, series, bins=None, show=None, compare=None):
  axis.set_title(nice_title(title, measures(series), measures(compare)), {'fontsize': 10})
  nb = bins if not bins is None else nice_bins(numpy.min(series), numpy.max(series))
  n, b, patch = axis.hist(series, nb)
  if not show is None:
    i = select_bin(show, b)
    if not i is None:
      patch[i].set_fc('r')
  if numpy.sum(n) > 0:
    if numpy.max(n) >= 1000:
      axis.yaxis.set_major_formatter(FuncFormatter(nf))
  else:
    axis.set_ylim(0, 1)

def nice_bars(axis, title, series, ticks=None, compare=None):
  axis.set_title(nice_title(title, sums_measures(series), sums_measures(compare)), {'fontsize': 10})
  axis.bar(series.index, series, 1, tick_label=ticks)
  if numpy.max(series) >= 1000:
    axis.yaxis.set_major_formatter(FuncFormatter(nf))

def nice_plot_page(page_title, plot_selectors, data, compare=None):
  h = math.ceil(len(plot_selectors) / 3)
  _, ax = pyplot.subplots(h, 3, figsize=(7, 10), gridspec_kw={ 'hspace': 0.6, 'wspace': 0.3 })
  pyplot.suptitle(page_title)
  i = 0
  cmp = compare or {}
  for item in plot_selectors:
    title, key = item[0], item[1]
    o = item[2] if len(item) > 2 else {}
    series = data.get(key)
    cmp_series = None
    if series is None:
      series = cmp.get(key)
    elif key in cmp:
      cmp_series = cmp.get(key)
    if series is None:
      pass
    elif key.endswith('_sums'):
      nice_bars(ax[i // 3, i % 3], title, series, o.get('ticks'), cmp_series)
    else:
      nice_hist(ax[i // 3, i % 3], title, series, o.get('range'), o.get('show'), cmp_series)
    i += 1
