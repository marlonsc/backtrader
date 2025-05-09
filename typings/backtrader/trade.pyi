from .utils import AutoOrderedDict as AutoOrderedDict
from .utils.date import num2date as num2date
from .utils.py3 import range as range
from _typeshed import Incomplete

class TradeHistory(AutoOrderedDict):
    event: Incomplete
    def __init__(self, status, dt, barlen, size, price, value, pnl, pnlcomm, tz, event: Incomplete | None = None) -> None: ...
    def __reduce__(self): ...
    def doupdate(self, order, size, price, commission) -> None: ...
    def datetime(self, tz: Incomplete | None = None, naive: bool = True): ...

class Trade:
    refbasis: Incomplete
    status_names: Incomplete
    Created: Incomplete
    Open: Incomplete
    Closed: Incomplete
    ref: Incomplete
    data: Incomplete
    tradeid: Incomplete
    size: Incomplete
    price: Incomplete
    value: Incomplete
    commission: Incomplete
    pnl: float
    pnlcomm: float
    justopened: bool
    isopen: bool
    isclosed: bool
    baropen: int
    dtopen: float
    barclose: int
    dtclose: float
    barlen: int
    historyon: Incomplete
    history: Incomplete
    status: Incomplete
    def __init__(self, data: Incomplete | None = None, tradeid: int = 0, historyon: bool = False, size: int = 0, price: float = 0.0, value: float = 0.0, commission: float = 0.0) -> None: ...
    def __len__(self) -> int: ...
    def __bool__(self) -> bool: ...
    __nonzero__ = __bool__
    def getdataname(self): ...
    def open_datetime(self, tz: Incomplete | None = None, naive: bool = True): ...
    def close_datetime(self, tz: Incomplete | None = None, naive: bool = True): ...
    long: Incomplete
    def update(self, order, size, price, value, commission, pnl, comminfo) -> None: ...
