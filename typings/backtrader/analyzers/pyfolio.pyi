import backtrader as bt
from . import GrossLeverage as GrossLeverage, PositionsValue as PositionsValue, TimeReturn as TimeReturn, Transactions as Transactions
from _typeshed import Incomplete
from backtrader.utils.py3 import iteritems as iteritems

class PyFolio(bt.Analyzer):
    params: Incomplete
    def __init__(self) -> None: ...
    def stop(self) -> None: ...
    def get_pf_items(self): ...
