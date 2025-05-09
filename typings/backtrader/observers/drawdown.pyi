from .. import Observer as Observer
from _typeshed import Incomplete

class DrawDown(Observer):
    params: Incomplete
    lines: Incomplete
    plotinfo: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...
    def next(self) -> None: ...

class DrawDownLength(Observer):
    lines: Incomplete
    plotinfo: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...
    def next(self) -> None: ...

class DrawDown_Old(Observer):
    lines: Incomplete
    plotinfo: Incomplete
    plotlines: Incomplete
    maxdd: float
    peak: Incomplete
    def __init__(self) -> None: ...
    def next(self) -> None: ...
