from . import Indicator as Indicator, MovingAverage as MovingAverage
from _typeshed import Incomplete

class EnvelopeMixIn:
    lines: Incomplete
    params: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...

class _EnvelopeBase(Indicator):
    lines: Incomplete
    plotinfo: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...

class Envelope(_EnvelopeBase, EnvelopeMixIn): ...

movname: Incomplete
linename: Incomplete
newclsname: Incomplete
newaliases: Incomplete
newclsdoc: Incomplete
newclsdct: Incomplete
newcls: Incomplete
module: Incomplete
