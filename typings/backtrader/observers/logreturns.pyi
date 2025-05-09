import backtrader as bt
from _typeshed import Incomplete

__all__ = ['LogReturns', 'LogReturns2']

class LogReturns(bt.Observer):
    lines: Incomplete
    plotinfo: Incomplete
    params: Incomplete
    logret1: Incomplete
    def __init__(self) -> None: ...
    def next(self) -> None: ...

class LogReturns2(LogReturns):
    lines: Incomplete
    logret2: Incomplete
    def __init__(self) -> None: ...
    def next(self) -> None: ...
