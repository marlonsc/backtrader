from .. import Observer as Observer
from ..utils.py3 import with_metaclass as with_metaclass
from _typeshed import Incomplete

class Trades(Observer):
    lines: Incomplete
    params: Incomplete
    plotinfo: Incomplete
    plotlines: Incomplete
    trades: int
    trades_long: int
    trades_short: int
    trades_plus: int
    trades_minus: int
    trades_plus_gross: int
    trades_minus_gross: int
    trades_win: int
    trades_win_max: int
    trades_win_min: int
    trades_loss: int
    trades_loss_max: int
    trades_loss_min: int
    trades_length: int
    trades_length_max: int
    trades_length_min: int
    def __init__(self) -> None: ...
    def next(self) -> None: ...

class MetaDataTrades(Observer.__class__):
    def donew(cls, *args, **kwargs): ...

class DataTrades(Incomplete):
    params: Incomplete
    plotinfo: Incomplete
    plotlines: Incomplete
    def next(self) -> None: ...
