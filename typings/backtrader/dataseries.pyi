from .lineseries import LineSeries as LineSeries
from .utils import AutoOrderedDict as AutoOrderedDict, OrderedDict as OrderedDict, date2num as date2num
from .utils.py3 import range as range
from _typeshed import Incomplete

class TimeFrame:
    Ticks: Incomplete
    MicroSeconds: Incomplete
    Seconds: Incomplete
    Minutes: Incomplete
    Days: Incomplete
    Weeks: Incomplete
    Months: Incomplete
    Years: Incomplete
    NoTimeFrame: Incomplete
    Names: Incomplete
    names = Names
    @classmethod
    def getname(cls, tframe, compression: Incomplete | None = None): ...
    @classmethod
    def TFrame(cls, name): ...
    @classmethod
    def TName(cls, tframe): ...

class DataSeries(LineSeries):
    plotinfo: Incomplete
    Close: Incomplete
    Low: Incomplete
    High: Incomplete
    Open: Incomplete
    Volume: Incomplete
    OpenInterest: Incomplete
    DateTime: Incomplete
    LineOrder: Incomplete
    def getwriterheaders(self): ...
    def getwritervalues(self): ...
    def getwriterinfo(self): ...

class OHLC(DataSeries):
    lines: Incomplete

class OHLCDateTime(OHLC):
    lines: Incomplete

class SimpleFilterWrapper:
    ffilter: Incomplete
    args: Incomplete
    kwargs: Incomplete
    def __init__(self, data, ffilter, *args, **kwargs) -> None: ...
    def __call__(self, data): ...

class _Bar(AutoOrderedDict):
    replaying: bool
    MAXDATE: Incomplete
    def __init__(self, maxdate: bool = False) -> None: ...
    close: Incomplete
    low: Incomplete
    high: Incomplete
    open: Incomplete
    volume: float
    openinterest: float
    datetime: Incomplete
    def bstart(self, maxdate: bool = False) -> None: ...
    def isopen(self): ...
    def bupdate(self, data, reopen: bool = False): ...
