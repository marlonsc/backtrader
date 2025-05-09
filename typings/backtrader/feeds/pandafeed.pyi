import backtrader.feed as feed
from _typeshed import Incomplete
from backtrader import date2num as date2num
from backtrader.utils.py3 import filter as filter, integer_types as integer_types, string_types as string_types

class PandasDirectData(feed.DataBase):
    params: Incomplete
    datafields: Incomplete
    def start(self) -> None: ...

class PandasData(feed.DataBase):
    params: Incomplete
    datafields: Incomplete
    def __init__(self) -> None: ...
    def start(self) -> None: ...
