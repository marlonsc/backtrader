from .mabase import MovAv as MovAv
from _typeshed import Incomplete
from backtrader.indicator import Indicator as Indicator

class BollingerBands(Indicator):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    plotinfo: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...

class BollingerBandsPct(BollingerBands):
    lines: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...
