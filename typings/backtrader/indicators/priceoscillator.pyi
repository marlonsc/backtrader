from . import Indicator as Indicator, MovAv as MovAv
from _typeshed import Incomplete

class _PriceOscBase(Indicator):
    params: Incomplete
    plotinfo: Incomplete
    ma1: Incomplete
    ma2: Incomplete
    def __init__(self) -> None: ...

class PriceOscillator(_PriceOscBase):
    alias: Incomplete
    lines: Incomplete

class PercentagePriceOscillator(_PriceOscBase):
    alias: Incomplete
    lines: Incomplete
    params: Incomplete
    plotlines: Incomplete
    def __init__(self) -> None: ...

class PercentagePriceOscillatorShort(PercentagePriceOscillator):
    alias: Incomplete
