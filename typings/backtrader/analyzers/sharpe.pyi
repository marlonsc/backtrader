from _typeshed import Incomplete
from backtrader import Analyzer as Analyzer, TimeFrame as TimeFrame
from backtrader.analyzers import AnnualReturn as AnnualReturn, TimeReturn as TimeReturn
from backtrader.mathsupport import average as average, standarddev as standarddev
from backtrader.utils.py3 import itervalues as itervalues

class SharpeRatio(Analyzer):
    params: Incomplete
    RATEFACTORS: Incomplete
    anret: Incomplete
    timereturn: Incomplete
    def __init__(self) -> None: ...
    ratio: Incomplete
    def stop(self) -> None: ...

class SharpeRatio_A(SharpeRatio):
    params: Incomplete
