from . import PeriodN
from _typeshed import Incomplete

__all__ = ['OLS_Slope_InterceptN', 'OLS_TransformationN', 'OLS_BetaN', 'CointN']

class OLS_Slope_InterceptN(PeriodN):
    packages: Incomplete
    lines: Incomplete
    params: Incomplete
    def next(self) -> None: ...

class OLS_TransformationN(PeriodN):
    lines: Incomplete
    params: Incomplete
    def __init__(self) -> None: ...

class OLS_BetaN(PeriodN):
    packages: Incomplete
    lines: Incomplete
    params: Incomplete
    def next(self) -> None: ...

class CointN(PeriodN):
    packages: Incomplete
    frompackages: Incomplete
    lines: Incomplete
    params: Incomplete
    def next(self) -> None: ...
