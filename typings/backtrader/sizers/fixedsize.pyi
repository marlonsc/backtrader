import backtrader as bt
from _typeshed import Incomplete

class FixedSize(bt.Sizer):
    params: Incomplete
    def setsizing(self, stake) -> None: ...
SizerFix = FixedSize

class FixedReverser(bt.Sizer):
    params: Incomplete

class FixedSizeTarget(bt.Sizer):
    params: Incomplete
    def setsizing(self, stake) -> None: ...
