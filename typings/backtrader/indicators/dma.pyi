from .mabase import MovAv as MovAv, MovingAverageBase as MovingAverageBase
from .zlind import ZeroLagIndicator as ZeroLagIndicator
from _typeshed import Incomplete

class DicksonMovingAverage(MovingAverageBase):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    def __init__(self) -> None: ...
DMA = DicksonMovingAverage
