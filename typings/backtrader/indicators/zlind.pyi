from . import MovAv as MovAv, MovingAverageBase as MovingAverageBase
from _typeshed import Incomplete
from backtrader.utils.py3 import MAXINT as MAXINT

class ZeroLagIndicator(MovingAverageBase):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    ema: Incomplete
    limits: Incomplete
    def __init__(self) -> None: ...
    def next(self) -> None: ...
