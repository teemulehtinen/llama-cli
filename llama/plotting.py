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

def nice_hist(axis, title, series, bins):
  axis.set_title(title)
  n, _, _ = axis.hist(series, bins)
  cx = (bins[0] + bins[-1]) / 2
  txt = f'N = {series.shape[0]}'
  if numpy.sum(n) > 0:
    axis.text(cx, 0.9 * numpy.max(n), txt, ha='center', va='center')
  else:
    axis.set_ylim(0, 1)
    axis.text(cx, 0.9, txt, ha='center', va='center')
