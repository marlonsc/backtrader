from .. import TimeFrame as TimeFrame, feed as feed
from ..utils import date2num as date2num
from ..utils.py3 import integer_types as integer_types, string_types as string_types
from _typeshed import Incomplete

class GenericCSVData(feed.CSVDataBase):
    params: Incomplete
    def start(self): ...

class GenericCSV(feed.CSVFeedBase):
    DataCls = GenericCSVData
