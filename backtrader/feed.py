"""feed.py module.

Description of the module functionality."""

# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2024 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import collections
import datetime
import inspect
import io
import os.path

from . import (
    dataseries,
    metabase,
)
from .dataseries import SimpleFilterWrapper, TimeFrame
from .resamplerfilter import Replayer, Resampler
from .tradingcal import PandasMarketCalendar
from .utils.date import Localizer, date2num, num2date, time2num, tzparse
from .utils.py3 import range, string_types, with_metaclass, zip


class MetaAbstractDataBase(type):
    """Metaclass for registering and initializing data feed subclasses."""

    _indcol = dict()

"""__init__ function.

Args:
    name: Description of name
    bases: Description of bases
    dct: Description of dct

Returns:
    Description of return value
"""
        super().__init__(name, bases, dct)
        if (
            not getattr(self, "aliased", False)
            and name != "DataBase"
            and not name.startswith("_")
        ):
            self._indcol[name] = self

"""dopreinit function.

Args:
    _obj: Description of _obj

Returns:
    Description of return value
"""
        _obj._feed = metabase.findowner(_obj, FeedBase)
        _obj.notifs = collections.deque()  # store notifications for cerebro
        _obj._dataname = _obj.p.dataname
        _obj._name = ""
        return _obj, args, kwargs

"""dopostinit function.

Args:
    _obj: Description of _obj

Returns:
    Description of return value
"""
        _obj._name = _obj._name or _obj.p.name
        if not _obj._name and isinstance(_obj.p.dataname, string_types):
            _obj._name = _obj.p.dataname
        _obj._compression = _obj.p.compression
        _obj._timeframe = _obj.p.timeframe
        if isinstance(_obj.p.sessionstart, datetime.datetime):
            _obj.p.sessionstart = _obj.p.sessionstart.time()
        elif _obj.p.sessionstart is None:
            _obj.p.sessionstart = datetime.time.min
        if isinstance(_obj.p.sessionend, datetime.datetime):
            _obj.p.sessionend = _obj.p.sessionend.time()
        elif _obj.p.sessionend is None:
            _obj.p.sessionend = datetime.time(23, 59, 59, 999990)
        if isinstance(_obj.p.fromdate, datetime.date):
            if not hasattr(_obj.p.fromdate, "hour"):
                _obj.p.fromdate = datetime.datetime.combine(
                    _obj.p.fromdate, _obj.p.sessionstart
                )
        if isinstance(_obj.p.todate, datetime.date):
            if not hasattr(_obj.p.todate, "hour"):
                _obj.p.todate = datetime.datetime.combine(
                    _obj.p.todate, _obj.p.sessionend
                )
        _obj._barstack = collections.deque()  # for filter operations
        _obj._barstash = collections.deque()  # for filter operations
        _obj._filters = list()
        _obj._ffilters = list()
        for fp in _obj.p.filters:
            if inspect.isclass(fp):
                fp = fp(_obj)
                if hasattr(fp, "last"):
                    _obj._ffilters.append((fp, [], {}))
            _obj._filters.append((fp, [], {}))
        return _obj, args, kwargs


class AbstractDataBase(with_metaclass(MetaAbstractDataBase, dataseries.OHLCDateTime)):
    """Abstract base class for all data feeds."""

    params = (
        ("dataname", None),
        ("name", ""),
        ("compression", 1),
        ("timeframe", TimeFrame.Days),
        ("fromdate", ""),  # 保持与ib的兼容，使用''表示不指定具体日期
        ("todate", ""),
        ("sessionstart", None),
        ("sessionend", None),
        ("filters", []),
        ("tz", None),
        ("tzinput", None),
        ("qcheck", 0.0),  # timeout in seconds (float) to check for events
        ("calendar", None),
    )

    (
        CONNECTED,
        DISCONNECTED,
        CONNBROKEN,
        DELAYED,
        LIVE,
        NOTSUBSCRIBED,
        NOTSUPPORTED_TF,
        UNKNOWN,
    ) = range(8)

    _NOTIFNAMES = [
        "CONNECTED",
        "DISCONNECTED",
        "CONNBROKEN",
        "DELAYED",
        "LIVE",
        "NOTSUBSCRIBED",
        "NOTSUPPORTED_TIMEFRAME",
        "UNKNOWN",
    ]

    @classmethod
    def _getstatusname(cls, status):
"""Args::
    status:"""
""""""
""""""
""""""
        """Returns the next eos using a trading calendar if available"""
        if self._clone:
            return self.data._getnexteos()
        if not len(self):
            return datetime.datetime.min, 0.0
        # Ensure self.lines is the correct object type before accessing .datetime
        if hasattr(self.lines, "datetime"):
            dt = self.lines.datetime[0]
        else:
            dt = 0.0
        dtime = num2date(dt)
        if self._calendar is None:
            nexteos = datetime.datetime.combine(dtime, self.p.sessionend)
            nextdteos = self.date2num(nexteos)
            nexteos = num2date(nextdteos)
            while dtime > nexteos:
                nexteos += datetime.timedelta(days=1)
            nextdteos = date2num(nexteos)
        else:
            # Remove 'calendar' keyword argument if present
            if isinstance(self._calendar, str):
                self._calendar = PandasMarketCalendar(self._calendar)
            _, nexteos = self._calendar.schedule(dtime, self._tz)
            nextdteos = date2num(nexteos)
        return nexteos, nextdteos

    def _gettzinput(self):
        """Can be overriden by classes to return a timezone for input"""
        return tzparse(self.p.tzinput)

    def _gettz(self):
"""To be overriden by subclasses which may auto-calculate the
        timezone"""
        """
        return tzparse(self.p.tz)

    def date2num(self, dt):
"""Args::
    dt:"""
"""Args::
    dt: (Default value = None)
    tz: (Default value = None)
    naive: (Default value = True)"""
    naive: (Default value = True)"""
        if dt is None:
            if hasattr(self.lines, "datetime"):
                return num2date(self.lines.datetime[0], tz or self._tz, naive)
            return num2date(0.0, tz or self._tz, naive)
        return num2date(dt, tz or self._tz, naive)

    def haslivedata(self):
""""""
"""Args::
    onoff: 
    qlapse:"""
    qlapse:"""
        # if onoff is True the data will wait p.qcheck for incoming live data
        # on its queue.
        qwait = self.p.qcheck if onoff else 0.0
        qwait = max(0.0, qwait - qlapse)
        self._qcheck = qwait

    def islive(self):
"""If this returns True, ``Cerebro`` will deactivate ``preload`` and
        ``runonce`` because a live data source must be fetched tick by tick (or
        bar by bar)"""
        """
        return False

    def put_notification(self, status, *args, **kwargs):
"""Add arguments to notification queue

Args::
    status:"""
    status:"""
        if self._laststatus != status:
            self.notifs.append((status, args, kwargs))
            self._laststatus = status

    def get_notifications(self):
""""""
""""""
"""Args::
    savemem: (Default value = 0)
    replaying: (Default value = False)"""
    replaying: (Default value = False)"""
        extrasize = self.resampling or replaying
        # Ensure self.lines is iterable and its elements have qbuffer
        for line in self.lines if hasattr(self.lines, "__iter__") else []:
            if hasattr(line, "qbuffer"):
                line.qbuffer(savemem=savemem, extrasize=extrasize)

    def start(self):
""""""
""""""
        """"""
        # Remove 'dataname' from kwargs if present
        kwargs.pop("dataname", None)
        return DataClone(**kwargs)

    def copyas(self, _dataname, **kwargs):
"""Args::
    _dataname:"""
"""Keep a reference to the environment

Args::
    env:"""
    env:"""
        self._env = env

    def getenvironment(self):
""""""
"""Args::
    f:"""
"""Args::
    p:"""
"""Call it to let the broker know that actions on this asset will
compensate open positions in another

Args::
    other:"""
    other:"""

        self._compensate = other

    def _tick_nullify(self):
""""""
"""Args::
    force: (Default value = False)"""
""""""
"""Args::
    size: (Default value = 1)
    datamaster: (Default value = None)
    ticks: (Default value = True)"""
    ticks: (Default value = True)"""
        if ticks:
            self._tick_nullify()

        # Need intercepting this call to support datas with
        # different lengths (timeframes)
        self.lines.advance(size)

        if datamaster is not None:
            if len(self) > self.buflen():
                # if no bar can be delivered, fill with an empty bar
                self.rewind()
                self.lines.forward()
                return

            if self.lines.datetime[0] > datamaster.lines.datetime[0]:
                self.lines.rewind()
            else:
                if ticks:
                    self._tick_fill()
        elif len(self) < self.buflen():
            # a resampler may have advance us past the last point
            if ticks:
                self._tick_fill()

    def next(self, datamaster=None, ticks=True):
"""Args::
    datamaster: (Default value = None)
    ticks: (Default value = True)"""
    ticks: (Default value = True)"""

        if len(self) >= self.buflen():
            if ticks:
                self._tick_nullify()

            # not preloaded - request next bar
            ret = self.load()
            if not ret:
                # if load cannot produce bars - forward the result
                return ret

            if datamaster is None:
                # bar is there and no master ... return load's result
                if ticks:
                    self._tick_fill()
                return ret
        else:
            self.advance(ticks=ticks)

        # a bar is "loaded" or was preloaded - index has been moved to it
        if datamaster is not None:
            # there is a time reference to check against
            if self.lines.datetime[0] > datamaster.lines.datetime[0]:
                # can't deliver new bar, too early, go back
                self.rewind()
                return False
            else:
                if ticks:
                    self._tick_fill()

        else:
            if ticks:
                self._tick_fill()

        # tell the world there is a bar (either the new or the previous
        return True

    def preload(self):
""""""
"""Args::
    datamaster: (Default value = None)"""
"""Args::
    forcedata: (Default value = None)"""
""""""
""""""
"""Saves given bar (list of values) to the stack for later retrieval

Args::
    bar: 
    stash: (Default value = False)"""
    stash: (Default value = False)"""
        if not stash:
            self._barstack.append(bar)
        else:
            self._barstash.append(bar)

    def _save2stack(self, erase=False, force=False, stash=False):
"""Saves current bar to the bar stack for later retrieval
Parameter ``erase`` determines removal from the data stream

Args::
    erase: (Default value = False)
    force: (Default value = False)
    stash: (Default value = False)"""
    stash: (Default value = False)"""
        bar = [line[0] for line in self.itersize()]
        if not stash:
            self._barstack.append(bar)
        else:
            self._barstash.append(bar)

        if erase:  # remove bar if requested
            self.backwards(force=force)

    def _updatebar(self, bar, forward=False, ago=0):
"""Load a value from the stack onto the lines to form the new bar
Returns True if values are present, False otherwise

Args::
    bar: 
    forward: (Default value = False)
    ago: (Default value = 0)"""
    ago: (Default value = 0)"""
        if forward:
            self.forward()

        for line, val in zip(self.itersize(), bar):
            line[0 + ago] = val

    def _fromstack(self, forward=False, stash=False):
"""Load a value from the stack onto the lines to form the new bar
Returns True if values are present, False otherwise

Args::
    forward: (Default value = False)
    stash: (Default value = False)"""
    stash: (Default value = False)"""

        coll = self._barstack if not stash else self._barstash

        if coll:
            if forward:
                self.forward()

            for line, val in zip(self.itersize(), coll.popleft()):
                line[0] = val

            return True

        return False

    def resample(self, **kwargs):
        """"""
        self.addfilter(Resampler, **kwargs)

    def replay(self, **kwargs):
        """"""
        self.addfilter(Replayer, **kwargs)


class DataBase(AbstractDataBase):
""""""
    """Base class for all feed containers."""

    params = getattr(DataBase.params, "_gettuple", lambda: DataBase.params)()
    DataCls = None  # Ensure DataCls is always present

"""__init__ function.

Returns:
    Description of return value
"""
        self.datas = list()

"""start function.

Returns:
    Description of return value
"""
        for data in self.datas:
            data.start()

"""stop function.

Returns:
    Description of return value
"""
        for data in self.datas:
            data.stop()

"""getdata function.

Args:
    dataname: Description of dataname
    name: Description of name

Returns:
    Description of return value
"""
        # Only access self.p if it exists
        if hasattr(self, "p"):
            for pname, pvalue in self.p._getitems():
                kwargs.setdefault(pname, getattr(self.p, pname))
        kwargs["dataname"] = dataname
        data = self._getdata(**kwargs)
        if data is not None:
            data._name = name
            self.datas.append(data)
        return data

"""_getdata function.

Args:
    dataname: Description of dataname

Returns:
    Description of return value
"""
        if hasattr(self, "p"):
            for pname, pvalue in self.p._getitems():
                kwargs.setdefault(pname, getattr(self.p, pname))
        kwargs["dataname"] = dataname
        if hasattr(self, "DataCls") and self.DataCls is not None:
            return self.DataCls(**kwargs)
        return None


class MetaCSVDataBase(type):
    """Metaclass for CSVDataBase."""

"""dopostinit function.

Args:
    cls: Description of cls
    _obj: Description of _obj

Returns:
    Description of return value
"""
        if not _obj.p.name and not _obj._name:
            _obj._name, _ = os.path.splitext(os.path.basename(_obj.p.dataname))
        # No super().dopostinit, as base type does not have it
        return _obj, args, kwargs


class CSVDataBase(with_metaclass(MetaCSVDataBase, DataBase)):
    """Base class for classes implementing CSV DataFeeds."""

    f = None
    params = (
        ("headers", True),
        ("separator", ","),
    )

    def start(self):
""""""
""""""
""""""
""""""
""""""
    """Base class for CSV feed containers."""

    params = ("basepath", "") + tuple(
        getattr(CSVDataBase.params, "_gettuple", lambda: CSVDataBase.params)()
    )

"""_getdata function.

Args:
    dataname: Description of dataname

Returns:
    Description of return value
"""
        return (
            self.DataCls(dataname=self.p.basepath + dataname, **self.p._getkwargs())
            if hasattr(self, "DataCls") and hasattr(self, "p")
            else None
        )


class DataClone(AbstractDataBase):
""""""
""""""
""""""
""""""
""""""
""""""
"""Args::
    size: (Default value = 1)
    datamaster: (Default value = None)
    ticks: (Default value = True)"""
    ticks: (Default value = True)"""
        self._dlen += size
        super(DataClone, self).advance(size, datamaster, ticks=ticks)
