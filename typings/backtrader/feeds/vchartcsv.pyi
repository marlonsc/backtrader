from .. import TimeFrame as TimeFrame, feed as feed
from ..utils import date2num as date2num
from _typeshed import Incomplete

class VChartCSVData(feed.CSVDataBase):
    vctframes: Incomplete

class VChartCSV(feed.CSVFeedBase):
    DataCls = VChartCSVData
