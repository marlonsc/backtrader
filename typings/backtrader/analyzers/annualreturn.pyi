from _typeshed import Incomplete
from backtrader import Analyzer as Analyzer
from backtrader.utils.py3 import range as range

class AnnualReturn(Analyzer):
    rets: Incomplete
    ret: Incomplete
    def stop(self) -> None: ...
    def get_analysis(self): ...
