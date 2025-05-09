from _typeshed import Incomplete
from backtrader import Analyzer as Analyzer
from backtrader.mathsupport import average as average, standarddev as standarddev
from backtrader.utils import AutoOrderedDict as AutoOrderedDict

class SQN(Analyzer):
    alias: Incomplete
    rets: Incomplete
    def create_analysis(self) -> None: ...
    pnl: Incomplete
    count: int
    def start(self) -> None: ...
    def notify_trade(self, trade) -> None: ...
    def stop(self) -> None: ...
