from .. import metabase as metabase
from _typeshed import Incomplete
from backtrader import TimeFrame as TimeFrame
from backtrader.utils.py3 import with_metaclass as with_metaclass

class SessionFiller(Incomplete):
    params: Incomplete
    MAXDATE: Incomplete
    seenbar: bool
    sessend: Incomplete
    def __init__(self, data) -> None: ...
    dtime_prev: Incomplete
    def __call__(self, data): ...

class SessionFilterSimple(Incomplete):
    def __init__(self, data) -> None: ...
    def __call__(self, data): ...

class SessionFilter(Incomplete):
    def __init__(self, data) -> None: ...
    def __call__(self, data): ...
