import numpy
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages

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

def nice_hist(axis, title, series, bins=None, color=None):
  axis.set_title(title)
  nb = bins if not bins is None else nice_bins(numpy.min(series), numpy.max(series))
  n, _, _ = axis.hist(series, nb, color=color)
  cx = (nb[0] + nb[-1]) / 2
  txt = f'N = {series.shape[0]}'
  if numpy.sum(n) > 0:
    axis.text(cx, 0.9 * numpy.max(n), txt, ha='center', va='center')
  else:
    axis.set_ylim(0, 1)
    axis.text(cx, 0.9, txt, ha='center', va='center')

def nice_bars(axis, title, series, ticks=None):
  axis.set_title(title)
  axis.bar(series.index, series, 1, tick_label=ticks)
