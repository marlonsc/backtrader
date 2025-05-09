from .basicops import And as And, If as If
from .mabase import MovAv as MovAv
from _typeshed import Incomplete
from backtrader.indicator import Indicator as Indicator

class UpMove(Indicator):
    lines: Incomplete
    def __init__(self) -> None: ...

class DownMove(Indicator):
    lines: Incomplete
    def __init__(self) -> None: ...

class _DirectionalIndicator(Indicator):
    params: Incomplete
    plotlines: Incomplete
    DIplus: Incomplete
    DIminus: Incomplete
    def __init__(self, _plus: bool = True, _minus: bool = True) -> None: ...

class DirectionalIndicator(_DirectionalIndicator):
    alias: Incomplete
    lines: Incomplete
    def __init__(self) -> None: ...

class PlusDirectionalIndicator(_DirectionalIndicator):
    alias: Incomplete
    lines: Incomplete
    plotinfo: Incomplete
    def __init__(self) -> None: ...

class MinusDirectionalIndicator(_DirectionalIndicator):
    alias: Incomplete
    lines: Incomplete
    plotinfo: Incomplete
    def __init__(self) -> None: ...

class AverageDirectionalMovementIndex(_DirectionalIndicator):
    alias: Incomplete
    lines: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...

class AverageDirectionalMovementIndexRating(AverageDirectionalMovementIndex):
    alias: Incomplete
    lines: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...

class DirectionalMovementIndex(AverageDirectionalMovementIndex, DirectionalIndicator):
    alias: Incomplete

class DirectionalMovement(AverageDirectionalMovementIndexRating, DirectionalIndicator):
    alias: Incomplete
