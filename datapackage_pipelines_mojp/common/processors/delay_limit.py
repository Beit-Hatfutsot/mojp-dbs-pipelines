from datapackage_pipelines_mojp.common.processors.base_processors import BaseProcessor
import datetime

class DelayLimit(BaseProcessor):
  
  def __init__(self, *args, **kwargs):
        super(Processor, self).__init__(*args, **kwargs)
        self.start_time = datetime.datetime.now()

  def get_daley_limit(self):
    return self._parameters.get("stop_after_minutes")

  def get_time_gap(self):
    current = datetime.datetime.now()
    minutes = (current - self.start_time).total_seconds() / 60
    return minutes
  
  def _filter_resource(self, resource_descriptor, resource_data):
    delay_limit = self._parameters.get("stop_after_minutes")
    for row in resource_data:
      time_gap = self.get_time_gap()
      row = self._filter_row(row)
      if time_gap > delay_limit:
        break

if __name__ == '__main__':
    DelayLimit.main()
