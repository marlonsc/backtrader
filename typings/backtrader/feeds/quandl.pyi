from .. import feed
from _typeshed import Incomplete

__all__ = ['QuandlCSV', 'Quandl']

class QuandlCSV(feed.CSVDataBase):
    params: Incomplete
    f: Incomplete
    def start(self) -> None: ...

class Quandl(QuandlCSV):
    params: Incomplete
    error: Incomplete
    f: Incomplete
    def start(self) -> None: ...
