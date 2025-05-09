from .. import Observer as Observer
from _typeshed import Incomplete

class Cash(Observer):
    lines: Incomplete
    plotinfo: Incomplete
    def next(self) -> None: ...

class Value(Observer):
    params: Incomplete
    lines: Incomplete
    plotinfo: Incomplete
    def start(self) -> None: ...
    def next(self) -> None: ...

class Broker(Observer):
    params: Incomplete
    alias: Incomplete
    lines: Incomplete
    plotinfo: Incomplete
    def start(self) -> None: ...
    def next(self) -> None: ...

class FundValue(Observer):
    alias: Incomplete
    lines: Incomplete
    plotinfo: Incomplete
    def next(self) -> None: ...

class FundShares(Observer):
    lines: Incomplete
    plotinfo: Incomplete
    def next(self) -> None: ...
