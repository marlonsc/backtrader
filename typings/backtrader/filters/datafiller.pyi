from _typeshed import Incomplete
from backtrader import AbstractDataBase as AbstractDataBase, TimeFrame as TimeFrame

class DataFiller(AbstractDataBase):
    params: Incomplete
    def start(self) -> None: ...
    def preload(self) -> None: ...
