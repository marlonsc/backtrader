from . import FindFirstIndexHighest as FindFirstIndexHighest, FindFirstIndexLowest as FindFirstIndexLowest, Indicator as Indicator
from _typeshed import Incomplete

class _AroonBase(Indicator):
    params: Incomplete
    plotinfo: Incomplete
    up: Incomplete
    down: Incomplete
    def __init__(self) -> None: ...

class AroonUp(_AroonBase):
    lines: Incomplete
    def __init__(self) -> None: ...

class AroonDown(_AroonBase):
    lines: Incomplete
    def __init__(self) -> None: ...

class AroonUpDown(AroonUp, AroonDown):
    alias: Incomplete

class AroonOscillator(_AroonBase):
    alias: Incomplete
    lines: Incomplete
    def __init__(self) -> None: ...

class AroonUpDownOscillator(AroonUpDown, AroonOscillator):
    alias: Incomplete
