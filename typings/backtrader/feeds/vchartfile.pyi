import backtrader as bt
from _typeshed import Incomplete
from backtrader import date2num as date2num

class MetaVChartFile(bt.DataBase.__class__):
    def __init__(cls, name, bases, dct) -> None: ...

class VChartFile(Incomplete):
    f: Incomplete
    def start(self) -> None: ...
    def stop(self) -> None: ...
