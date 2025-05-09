from .. import TimeFrame as TimeFrame, feed as feed
from ..utils import date2num as date2num
from _typeshed import Incomplete

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
