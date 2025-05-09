from .. import feed as feed
from ..utils import date2num as date2num
from ..utils.py3 import urlquote as urlquote
from _typeshed import Incomplete

class YahooFinanceCSVData(feed.CSVDataBase):
    lines: Incomplete
    params: Incomplete
    f: Incomplete
    def start(self) -> None: ...

class YahooLegacyCSV(YahooFinanceCSVData):
    params: Incomplete

class YahooFinanceCSV(feed.CSVFeedBase):
    DataCls = YahooFinanceCSVData

class YahooFinanceData(YahooFinanceCSVData):
    params: Incomplete
    error: Incomplete
    f: Incomplete
    def start_v7(self) -> None: ...
    def start(self) -> None: ...

class YahooFinance(feed.CSVFeedBase):
    DataCls = YahooFinanceData
    params: Incomplete
