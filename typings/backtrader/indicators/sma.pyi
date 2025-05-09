from .basicops import Average as Average
from .mabase import MovAv as MovAv, MovingAverageBase as MovingAverageBase
from _typeshed import Incomplete

class MovingAverageSimple(MovingAverageBase):
    alias: Incomplete
    lines: Incomplete
    def __init__(self) -> None: ...
