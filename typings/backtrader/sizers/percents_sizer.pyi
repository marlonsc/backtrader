import backtrader as bt
from _typeshed import Incomplete

__all__ = ['PercentSizer', 'AllInSizer', 'PercentSizerInt', 'AllInSizerInt']

class PercentSizer(bt.Sizer):
    params: Incomplete
    def __init__(self) -> None: ...

class AllInSizer(PercentSizer):
    params: Incomplete

class PercentSizerInt(PercentSizer):
    params: Incomplete

class AllInSizerInt(PercentSizerInt):
    params: Incomplete
