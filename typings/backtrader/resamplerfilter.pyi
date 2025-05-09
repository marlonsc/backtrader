from . import metabase as metabase
from .dataseries import TimeFrame as TimeFrame
from .utils.date import date2num as date2num, num2date as num2date
from .utils.py3 import with_metaclass as with_metaclass
from _typeshed import Incomplete

class DTFaker:
    data: Incomplete
    p: Incomplete
    sessionend: Incomplete
    def __init__(self, data, forcedata: Incomplete | None = None) -> None: ...
    def __len__(self) -> int: ...
    def __call__(self, idx: int = 0): ...
    def datetime(self, idx: int = 0): ...
    def date(self, idx: int = 0): ...
    def time(self, idx: int = 0): ...
    def __getitem__(self, idx): ...
    def num2date(self, *args, **kwargs): ...
    def date2num(self, *args, **kwargs): ...

class _BaseResampler(Incomplete):
    params: Incomplete
    subdays: Incomplete
    subweeks: Incomplete
    componly: Incomplete
    bar: Incomplete
    compcount: int
    doadjusttime: Incomplete
    data: Incomplete
    def __init__(self, data) -> None: ...
    def check(self, data, _forcedata: Incomplete | None = None): ...

class Resampler(_BaseResampler):
    params: Incomplete
    replaying: bool
    def last(self, data): ...
    def __call__(self, data, fromcheck: bool = False, forcedata: Incomplete | None = None): ...

class Replayer(_BaseResampler):
    params: Incomplete
    replaying: bool
    def __call__(self, data, fromcheck: bool = False, forcedata: Incomplete | None = None): ...

class ResamplerTicks(Resampler):
    params: Incomplete

class ResamplerSeconds(Resampler):
    params: Incomplete

class ResamplerMinutes(Resampler):
    params: Incomplete

class ResamplerDaily(Resampler):
    params: Incomplete

class ResamplerWeekly(Resampler):
    params: Incomplete

class ResamplerMonthly(Resampler):
    params: Incomplete

class ResamplerYearly(Resampler):
    params: Incomplete

class ReplayerTicks(Replayer):
    params: Incomplete

class ReplayerSeconds(Replayer):
    params: Incomplete

class ReplayerMinutes(Replayer):
    params: Incomplete

class ReplayerDaily(Replayer):
    params: Incomplete

class ReplayerWeekly(Replayer):
    params: Incomplete

class ReplayerMonthly(Replayer):
    params: Incomplete
