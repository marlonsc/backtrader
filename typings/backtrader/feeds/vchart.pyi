from .. import feed as feed
from _typeshed import Incomplete
from backtrader.dataseries import TimeFrame as TimeFrame
from backtrader.utils.dateintern import date2num as date2num

class VChartData(feed.DataBase):
    ext: str
    barsize: int
    dtsize: int
    barfmt: str
    f: Incomplete
    def start(self) -> None: ...
    def stop(self) -> None: ...

class VChartFeed(feed.FeedBase):
    DataCls = VChartData
    params: Incomplete
