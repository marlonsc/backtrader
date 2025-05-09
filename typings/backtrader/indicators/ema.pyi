from .basicops import ExponentialSmoothing as ExponentialSmoothing
from .mabase import MovAv as MovAv, MovingAverageBase as MovingAverageBase
from _typeshed import Incomplete

class ExponentialMovingAverage(MovingAverageBase):
    alias: Incomplete
    lines: Incomplete
    def __init__(self) -> None: ...
