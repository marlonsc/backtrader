import math
from ..utils.py3 import range as range
from _typeshed import Incomplete
from backtrader.indicator import Indicator as Indicator

class PeriodN(Indicator):
    params: Incomplete
    def __init__(self) -> None: ...

class OperationN(PeriodN):
    def next(self) -> None: ...
    def once(self, start, end) -> None: ...

class BaseApplyN(OperationN):
    params: Incomplete
    func: Incomplete
    def __init__(self) -> None: ...

class ApplyN(BaseApplyN):
    lines: Incomplete

class Highest(OperationN):
    alias: Incomplete
    lines: Incomplete
    func = max

class Lowest(OperationN):
    alias: Incomplete
    lines: Incomplete
    func = min

class ReduceN(OperationN):
    lines: Incomplete
    func: Incomplete
    def __init__(self, function, **kwargs) -> None: ...

class SumN(OperationN):
    lines: Incomplete
    func = math.fsum

class AnyN(OperationN):
    lines: Incomplete
    func = any

class AllN(OperationN):
    lines: Incomplete
    func = all

class FindFirstIndex(OperationN):
    lines: Incomplete
    params: Incomplete
    def func(self, iterable): ...

class FindFirstIndexHighest(FindFirstIndex):
    params: Incomplete

class FindFirstIndexLowest(FindFirstIndex):
    params: Incomplete

class FindLastIndex(OperationN):
    lines: Incomplete
    params: Incomplete
    def func(self, iterable): ...

class FindLastIndexHighest(FindLastIndex):
    params: Incomplete

class FindLastIndexLowest(FindLastIndex):
    params: Incomplete

class Accum(Indicator):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    def nextstart(self) -> None: ...
    def next(self) -> None: ...
    def oncestart(self, start, end) -> None: ...
    def once(self, start, end) -> None: ...

class Average(PeriodN):
    alias: Incomplete
    lines: Incomplete
    def next(self) -> None: ...
    def once(self, start, end) -> None: ...

class ExponentialSmoothing(Average):
    alias: Incomplete
    params: Incomplete
    alpha: Incomplete
    alpha1: Incomplete
    def __init__(self) -> None: ...
    def nextstart(self) -> None: ...
    def next(self) -> None: ...
    def oncestart(self, start, end) -> None: ...
    def once(self, start, end) -> None: ...

class ExponentialSmoothingDynamic(ExponentialSmoothing):
    alias: Incomplete
    def __init__(self) -> None: ...
    def next(self) -> None: ...
    def once(self, start, end) -> None: ...

class WeightedAverage(PeriodN):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    def __init__(self) -> None: ...
    def next(self) -> None: ...
    def once(self, start, end) -> None: ...

def And(*args): ...
def If(cond, true_val, false_val): ...
