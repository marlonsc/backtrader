from .basicops import ExponentialSmoothing as ExponentialSmoothing
from .mabase import MetaMovAvBase as MetaMovAvBase, MovAv as MovAv, MovingAverageBase as MovingAverageBase
from _typeshed import Incomplete

class SmoothedMovingAverage(MovingAverageBase, metaclass=MetaMovAvBase):
    alias: Incomplete
    lines: Incomplete
    def __init__(self) -> None: ...
