from . import Filter
from _typeshed import Incomplete

__all__ = ['Renko']

class Renko(Filter):
    params: Incomplete
    def nextstart(self, data) -> None: ...
    def next(self, data): ...
