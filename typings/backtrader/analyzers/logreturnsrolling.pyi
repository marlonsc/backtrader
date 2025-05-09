import backtrader as bt
from _typeshed import Incomplete

__all__ = ['LogReturnsRolling']

class LogReturnsRolling(bt.TimeFrameAnalyzerBase):
    params: Incomplete
    def start(self) -> None: ...
    def notify_fund(self, cash, value, fundvalue, shares) -> None: ...
    def next(self) -> None: ...
