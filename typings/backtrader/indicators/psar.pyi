from . import PeriodN
from _typeshed import Incomplete

__all__ = ['ParabolicSAR', 'PSAR']

class _SarStatus:
    sar: Incomplete
    tr: Incomplete
    af: float
    ep: float

class ParabolicSAR(PeriodN):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    plotinfo: Incomplete
    plotlines: Incomplete
    def prenext(self) -> None: ...
    def nextstart(self) -> None: ...
    def next(self) -> None: ...

# Names in __all__ with no definition:
#   PSAR
