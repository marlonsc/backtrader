from _typeshed import Incomplete
from backtrader import TimeFrameAnalyzerBase as TimeFrameAnalyzerBase

class Returns(TimeFrameAnalyzerBase):
    params: Incomplete
    def start(self) -> None: ...
    def stop(self) -> None: ...
