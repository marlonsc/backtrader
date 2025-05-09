from .. import feed as feed
from ..utils import date2num as date2num

class BacktraderCSVData(feed.CSVDataBase): ...

class BacktraderCSV(feed.CSVFeedBase):
    DataCls = BacktraderCSVData
