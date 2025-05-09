from .basicops import Highest as Highest, Lowest as Lowest
from .mabase import MovAv as MovAv
from .smma import SmoothedMovingAverage as SmoothedMovingAverage
from _typeshed import Incomplete
from backtrader.indicator import Indicator as Indicator

class TrueHigh(Indicator):
    lines: Incomplete
    def __init__(self) -> None: ...

class TrueLow(Indicator):
    lines: Incomplete
    def __init__(self) -> None: ...

class TrueRange(Indicator):
    alias: Incomplete
    lines: Incomplete
    def __init__(self) -> None: ...

class AverageTrueRange(Indicator):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    def __init__(self) -> None: ...
ATR = AverageTrueRange
