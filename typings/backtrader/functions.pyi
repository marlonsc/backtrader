import math
from .linebuffer import LineActions as LineActions
from .utils.py3 import cmp as cmp, range as range
from _typeshed import Incomplete

class List(list):
    def __contains__(self, other) -> bool: ...

class Logic(LineActions):
    args: Incomplete
    def __init__(self, *args) -> None: ...

class DivByZero(Logic):
    a: Incomplete
    b: Incomplete
    zero: Incomplete
    def __init__(self, a, b, zero: float = 0.0) -> None: ...
    def next(self) -> None: ...
    def once(self, start, end) -> None: ...

class DivZeroByZero(Logic):
    a: Incomplete
    b: Incomplete
    single: Incomplete
    dual: Incomplete
    def __init__(self, a, b, single=..., dual: float = 0.0) -> None: ...
    def next(self) -> None: ...
    def once(self, start, end) -> None: ...

class Cmp(Logic):
    a: Incomplete
    b: Incomplete
    def __init__(self, a, b) -> None: ...
    def next(self) -> None: ...
    def once(self, start, end) -> None: ...

class CmpEx(Logic):
    a: Incomplete
    b: Incomplete
    r1: Incomplete
    r2: Incomplete
    r3: Incomplete
    def __init__(self, a, b, r1, r2, r3) -> None: ...
    def next(self) -> None: ...
    def once(self, start, end) -> None: ...

class If(Logic):
    a: Incomplete
    b: Incomplete
    cond: Incomplete
    def __init__(self, cond, a, b) -> None: ...
    def next(self) -> None: ...
    def once(self, start, end) -> None: ...

class MultiLogic(Logic):
    def next(self) -> None: ...
    def once(self, start, end) -> None: ...

class MultiLogicReduce(MultiLogic):
    flogic: Incomplete
    def __init__(self, *args, **kwargs) -> None: ...

class Reduce(MultiLogicReduce):
    flogic: Incomplete
    def __init__(self, flogic, *args, **kwargs) -> None: ...

class And(MultiLogicReduce):
    flogic: Incomplete

class Or(MultiLogicReduce):
    flogic: Incomplete

class Max(MultiLogic):
    flogic = max

class Min(MultiLogic):
    flogic = min

class Sum(MultiLogic):
    flogic = math.fsum

class Any(MultiLogic):
    flogic = any

class All(MultiLogic):
    flogic = all
