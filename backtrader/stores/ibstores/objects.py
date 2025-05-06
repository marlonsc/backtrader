"""Object hierarchy."""

from dataclasses import dataclass, field
from datetime import date as date_
from datetime import datetime
from typing import List, NamedTuple, Optional, Union

from eventkit import Event

from .contract import Contract, ScanData, TagValue
from .util import EPOCH, UNSET_DOUBLE, UNSET_INTEGER

nan = float("nan")


@dataclass
class ScannerSubscription:
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
    """List of :class:`.BarData` that also stores all request parameters.
Events:
* ``updateEvent``
(bars: :class:`.BarDataList`, hasNewBar: bool)"""

    reqId: int
    contract: Contract
    endDateTime: Union[datetime, date_, str, None]
    durationStr: str
    barSizeSetting: str
    whatToShow: str
    useRTH: bool
    formatDate: int
    keepUpToDate: bool
    chartOptions: List[TagValue]

    def __init__(self, *args):
        """"""
        super().__init__(*args)
        self.updateEvent = Event("updateEvent")

    def __eq__(self, other):
"""Args::
    other:"""
""""""
    """List of :class:`.RealTimeBar` that also stores all request parameters.
Events:
* ``updateEvent``
(bars: :class:`.RealTimeBarList`, hasNewBar: bool)"""

    reqId: int
    contract: Contract
    barSize: int
    whatToShow: str
    useRTH: bool
    realTimeBarsOptions: List[TagValue]

    def __init__(self, *args):
        """"""
        super().__init__(*args)
        self.updateEvent = Event("updateEvent")

    def __eq__(self, other):
"""Args::
    other:"""
""""""
    """List of :class:`.ScanData` that also stores all request parameters.
Events:
* ``updateEvent`` (:class:`.ScanDataList`)"""

    reqId: int
    subscription: ScannerSubscription
    scannerSubscriptionOptions: List[TagValue]
    scannerSubscriptionFilterOptions: List[TagValue]

    def __init__(self, *args):
        """"""
        super().__init__(*args)
        self.updateEvent = Event("updateEvent")

    def __eq__(self, other):
"""Args::
    other:"""
""""""
""""""
        """"""
        self.__dict__.update(kwargs)

    def __repr__(self):
""""""
"""See:
    https://web.archive.org/web/20200725010343/https://interactivebrokers.github.io/tws-api/fundamental_ratios_tags.html"""
    """
