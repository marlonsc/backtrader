from .mabase import MovAv as MovAv, MovingAverageBase as MovingAverageBase
from _typeshed import Incomplete

class DoubleExponentialMovingAverage(MovingAverageBase):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    def __init__(self) -> None: ...

class TripleExponentialMovingAverage(MovingAverageBase):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    def __init__(self) -> None: ...
DEMA = DoubleExponentialMovingAverage
