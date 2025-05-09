from _typeshed import Incomplete
from backtrader.metabase import MetaParams as MetaParams
from backtrader.utils.py3 import MAXINT as MAXINT, with_metaclass as with_metaclass

class FixedSize(Incomplete):
    params: Incomplete
    def __call__(self, order, price, ago): ...

class FixedBarPerc(Incomplete):
    params: Incomplete
    def __call__(self, order, price, ago): ...

class BarPointPerc(Incomplete):
    params: Incomplete
    def __call__(self, order, price, ago): ...
