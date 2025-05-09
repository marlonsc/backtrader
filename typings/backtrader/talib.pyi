import backtrader as bt
from _typeshed import Incomplete
from backtrader.utils.py3 import with_metaclass as with_metaclass

MA_Type: Incomplete
R_TA_FUNC_FLAGS: Incomplete
FUNC_FLAGS_SAMESCALE: int
FUNC_FLAGS_UNSTABLE: int
FUNC_FLAGS_CANDLESTICK: int
R_TA_OUTPUT_FLAGS: Incomplete
OUT_FLAGS_LINE: int
OUT_FLAGS_DOTTED: int
OUT_FLAGS_DASH: int
OUT_FLAGS_HISTO: int
OUT_FLAGS_UPPER: int
OUT_FLAGS_LOWER: int

class _MetaTALibIndicator(bt.Indicator.__class__):
    def dopostinit(cls, _obj, *args, **kwargs): ...

class _TALibIndicator(Incomplete):
    CANDLEOVER: float
    CANDLEREF: int
    def oncestart(self, start, end) -> None: ...
    def once(self, start, end) -> None: ...
    def next(self) -> None: ...

tafunctions: Incomplete
