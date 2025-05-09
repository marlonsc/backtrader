from . import DivByZero as DivByZero, Highest as Highest, Indicator as Indicator, Lowest as Lowest, MovAv as MovAv
from _typeshed import Incomplete

class _StochasticBase(Indicator):
    lines: Incomplete
    params: Incomplete
    plotlines: Incomplete
    k: Incomplete
    d: Incomplete
    def __init__(self) -> None: ...

class StochasticFast(_StochasticBase):
    def __init__(self) -> None: ...

class Stochastic(_StochasticBase):
    alias: Incomplete
    params: Incomplete
    def __init__(self) -> None: ...

class StochasticFull(_StochasticBase):
    lines: Incomplete
    params: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...
