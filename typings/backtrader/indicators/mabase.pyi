from . import Indicator as Indicator
from ..utils.py3 import with_metaclass as with_metaclass
from _typeshed import Incomplete

class MovingAverage:
    @classmethod
    def register(cls, regcls) -> None: ...

class MovAv(MovingAverage): ...

class MetaMovAvBase(Indicator.__class__):
    def __new__(meta, name, bases, dct): ...

class MovingAverageBase(Incomplete):
    params: Incomplete
    plotinfo: Incomplete
