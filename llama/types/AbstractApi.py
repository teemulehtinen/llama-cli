class AbstractApi:

  def list_tables(self, try_cache=True, only_cache=False):
    raise NotImplementedError()
