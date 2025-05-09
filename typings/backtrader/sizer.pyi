from .metabase import MetaParams as MetaParams
from .utils.py3 import with_metaclass as with_metaclass
from _typeshed import Incomplete

class Sizer(Incomplete):
    strategy: Incomplete
    broker: Incomplete
    def getsizing(self, data, isbuy): ...
    def set(self, strategy, broker) -> None: ...
SizerBase = Sizer
