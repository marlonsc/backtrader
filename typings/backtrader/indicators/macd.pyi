from . import Indicator as Indicator, MovAv as MovAv
from _typeshed import Incomplete

class MACD(Indicator):
    lines: Incomplete
    params: Incomplete
    plotinfo: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...

class MACDHisto(MACD):
    alias: Incomplete
    lines: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...
