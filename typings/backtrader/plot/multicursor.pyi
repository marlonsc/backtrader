from ..utils.py3 import zip as zip
from _typeshed import Incomplete

class Widget:
    drawon: bool
    eventson: bool
    def set_active(self, active) -> None: ...
    def get_active(self): ...
    active: Incomplete
    def ignore(self, event): ...

class MultiCursor(Widget):
    canvas: Incomplete
    axes: Incomplete
    horizOn: Incomplete
    vertOn: Incomplete
    horizMulti: Incomplete
    vertMulti: Incomplete
    visible: bool
    useblit: Incomplete
    background: Incomplete
    needclear: bool
    vlines: Incomplete
    hlines: Incomplete
    def __init__(self, canvas, axes, useblit: bool = True, horizOn: bool = False, vertOn: bool = True, horizMulti: bool = False, vertMulti: bool = True, horizShared: bool = True, vertShared: bool = False, **lineprops) -> None: ...
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def clear(self, event) -> None: ...
    def onmove(self, event) -> None: ...

class MultiCursor2(Widget):
    canvas: Incomplete
    axes: Incomplete
    horizOn: Incomplete
    vertOn: Incomplete
    visible: bool
    useblit: Incomplete
    background: Incomplete
    needclear: bool
    vlines: Incomplete
    hlines: Incomplete
    def __init__(self, canvas, axes, useblit: bool = True, horizOn: bool = False, vertOn: bool = True, **lineprops) -> None: ...
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def clear(self, event) -> None: ...
    def onmove(self, event) -> None: ...
