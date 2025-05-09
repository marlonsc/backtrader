from . import PeriodN
from _typeshed import Incomplete

__all__ = ['LaguerreRSI', 'LRSI', 'LaguerreFilter', 'LAGF']

class LaguerreRSI(PeriodN):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    plotinfo: Incomplete
    l0: Incomplete
    l1: Incomplete
    l2: Incomplete
    l3: Incomplete
    def next(self) -> None: ...

class LaguerreFilter(PeriodN):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    plotinfo: Incomplete
    l0: Incomplete
    l1: Incomplete
    l2: Incomplete
    l3: Incomplete
    def next(self) -> None: ...

# Names in __all__ with no definition:
#   LAGF
#   LRSI
