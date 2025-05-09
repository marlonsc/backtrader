from _typeshed import Incomplete
from backtrader import Analyzer as Analyzer
from backtrader.utils import AutoDict as AutoDict, AutoOrderedDict as AutoOrderedDict
from backtrader.utils.py3 import MAXINT as MAXINT

class TradeAnalyzer(Analyzer):
    rets: Incomplete
    def create_analysis(self) -> None: ...
    def stop(self) -> None: ...
    def notify_trade(self, trade) -> None: ...
