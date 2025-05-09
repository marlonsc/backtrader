from ..observer import Observer as Observer
from _typeshed import Incomplete

class BuySell(Observer):
    lines: Incomplete
    plotinfo: Incomplete
    plotlines: Incomplete
    params: Incomplete
    curbuylen: int
    curselllen: int
    def next(self) -> None: ...
