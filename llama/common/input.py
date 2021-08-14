def input_selection(options):
  opt = list(options)
  n = 0
  while True:
    is_last = n + 10 > len(opt)
    for i in range(n, len(opt) if is_last else n + 10):
      print('{:d} = {}'.format(i, opt[i]))
    s = input('Enter index: ' if is_last else 'Enter index or \'m\' for more: ')
    if s == 'm' and not is_last:
      n += 10
    else:
      try:
        i = int(s)
        if 0 <= i < len(opt):
          return i
      except ValueError:
        pass
      return None
