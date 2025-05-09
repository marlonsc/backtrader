import backtrader as bt
from _typeshed import Incomplete

SIGNAL_NONE: Incomplete
SIGNAL_LONGSHORT: Incomplete
SIGNAL_LONG: Incomplete
SIGNAL_LONG_INV: Incomplete
SIGNAL_LONG_ANY: Incomplete
SIGNAL_SHORT: Incomplete
SIGNAL_SHORT_INV: Incomplete
SIGNAL_SHORT_ANY: Incomplete
SIGNAL_LONGEXIT: Incomplete
SIGNAL_LONGEXIT_INV: Incomplete
SIGNAL_LONGEXIT_ANY: Incomplete
SIGNAL_SHORTEXIT: Incomplete
SIGNAL_SHORTEXIT_INV: Incomplete
SIGNAL_SHORTEXIT_ANY: Incomplete
SignalTypes: Incomplete

class Signal(bt.Indicator):
    SignalTypes = SignalTypes
    lines: Incomplete
    def __init__(self) -> None: ...
