#!/usr/bin/env python
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
"""Analyzer module for Backtrader. Provides base classes and metaclasses for analyzers,
which are used to compute and report statistics and results from strategies."""
"""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import calendar
import datetime
import pprint as pp
from collections import OrderedDict

from . import TimeFrame
from .metabase import MetaParams, findowner
from .observer import Observer
from .strategy import Strategy
from .utils.py3 import MAXINT, with_metaclass
from .writer import WriterFile


class MetaAnalyzer(MetaParams):
"""Metaclass for Analyzer. Handles analyzer instantiation and parent/child
    registration. All docstrings and comments must be line-wrapped at 90 characters
    or less."""
    """

    def donew(cls, *args, **kwargs):
        """Intercept the strategy parameter"""
        # Create the object and set the params in place
        _obj, args, kwargs = super(MetaAnalyzer, cls).donew(*args, **kwargs)

        _obj._children = list()

        _obj.strategy = strategy = findowner(_obj, Strategy)
        _obj._parent = findowner(_obj, Analyzer)

        # Register with a master observer if created inside one
        masterobs = findowner(_obj, Observer)
        if masterobs is not None:
            masterobs._register_analyzer(_obj)

        _obj.datas = strategy.datas

        # For each data add aliases: for first data: data and data0
        if _obj.datas:
            _obj.data = data = _obj.datas[0]

            for line_idx, line in enumerate(data.lines):
                linealias = data._getlinealias(line_idx)
                if linealias:
                    setattr(_obj, f"data_{linealias}", line)
                setattr(_obj, f"data_{line_idx}", line)

            for data_idx, data in enumerate(_obj.datas):
                setattr(_obj, f"data{data_idx}", data)

                for line_idx, line in enumerate(data.lines):
                    linealias = data._getlinealias(line_idx)
                    if linealias:
                        setattr(_obj, f"data{data_idx}_{linealias}", line)
                    setattr(_obj, f"data{data_idx}_{line_idx}", line)

        _obj.create_analysis()

        # Return to the normal chain
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
"""Args::
    _obj:"""
    """Analyzer base class. All analyzers are subclass of this one.
Provides hooks for strategy notifications and analysis reporting.
All docstrings and comments must be line-wrapped at 90 characters or less.
An Analyzer instance operates in the frame of a strategy and provides an
analysis for that strategy.
Automagically set member attributes:
- ``self.strategy`` (giving access to the *strategy* and anything
accessible from it)
- ``self.datas[x]`` giving access to the array of data feeds present in
the the system, which could also be accessed via the strategy reference
- ``self.data``, giving access to ``self.datas[0]``
- ``self.dataX`` -> ``self.datas[X]``
- ``self.dataX_Y`` -> ``self.datas[X].lines[Y]``
- ``self.dataX_name`` -> ``self.datas[X].name``
- ``self.data_name`` -> ``self.datas[0].name``
- ``self.data_Y`` -> ``self.datas[0].lines[Y]``
This is not a *Lines* object, but the methods and operation follow the same
design
- ``__init__`` during instantiation and initial setup
- ``start`` / ``stop`` to signal the begin and end of operations
- ``prenext`` / ``nextstart`` / ``next`` family of methods that follow
the calls made to the same methods in the strategy
- ``notify_trade`` / ``notify_order`` / ``notify_cashvalue`` /
``notify_fund`` which receive the same notifications as the equivalent
methods of the strategy
The mode of operation is open and no pattern is preferred. As such the
analysis can be generated with the ``next`` calls, at the end of operations
during ``stop`` and even with a single method like ``notify_trade``
The important thing is to override ``get_analysis`` to return a *dict-like*
object containing the results of the analysis (the actual format is
implementation dependent)"""

    csv = True

"""__init__ function.

Returns:
    Description of return value
"""
        self.p = None  # Garante que self.p exista antes de qualquer acesso
        self._children = []
        self.strategy = None
        if not hasattr(self, "p") or self.p is None:
            param_dict = dict((k, v) for k, v in getattr(self, "params", []))
            self.p = type("Params", (), param_dict)()
        self.data = None
        super().__init__(*args, **kwargs)

    def __len__(self):
"""Support for invoking ``len`` on analyzers by actually returning the
        current length of the strategy the analyzer operates on"""
        """
        return len(self.strategy)

    def _register(self, child):
"""Args::
    child:"""
""""""
"""Args::
    cash: 
    value:"""
    value:"""
        for child in self._children:
            child._notify_cashvalue(cash, value)

        self.notify_cashvalue(cash, value)

    def _notify_fund(self, cash, value, fundvalue, shares):
"""Args::
    cash: 
    value: 
    fundvalue: 
    shares:"""
    shares:"""
        for child in self._children:
            child._notify_fund(cash, value, fundvalue, shares)

        self.notify_fund(cash, value, fundvalue, shares)

    def _notify_trade(self, trade):
"""Args::
    trade:"""
"""Args::
    order:"""
""""""
""""""
""""""
""""""
"""Receives the cash/value notification before each next cycle

Args::
    cash: 
    value:"""
    value:"""

    def notify_fund(self, cash, value, fundvalue, shares):
"""Receives the current cash, value, fundvalue and fund shares

Args::
    cash: 
    value: 
    fundvalue: 
    shares:"""
    shares:"""

    def notify_order(self, order):
"""Receives order notifications before each next cycle

Args::
    order:"""
    order:"""

    def notify_trade(self, trade):
"""Receives trade notifications before each next cycle

Args::
    trade:"""
    trade:"""

    def next(self):
"""Invoked for each next invocation of the strategy, once the minum
        preiod of the strategy has been reached"""
        """

    def prenext(self):
        """Invoked for each prenext invocation of the strategy, until the minimum
period of the strategy has been reached
The default behavior for an analyzer is to invoke ``next``"""
        self.next()

    def nextstart(self):
"""Invoked exactly once for the nextstart invocation of the strategy,
        when the minimum period has been first reached"""
        """
        self.next()

    def start(self):
"""Invoked to indicate the start of operations, giving the analyzer
        time to setup up needed things"""
        """

    def stop(self):
"""Invoked to indicate the end of operations, giving the analyzer
        time to shut down needed things"""
        """

    def create_analysis(self):
        """Meant to be overriden by subclasses. Gives a chance to create the
structures that hold the analysis.
The default behaviour is to create a ``OrderedDict`` named ``rets``"""
        self.rets = OrderedDict()

    def get_analysis(self):
        """Returns a *dict-like* object with the results of the analysis
The keys and format of analysis results in the dictionary is
implementation dependent.
It is not even enforced that the result is a *dict-like object*, just
the convention
The default implementation returns the default OrderedDict ``rets``
created by the default ``create_analysis`` method"""
        return self.rets

    def print(self, *args, **kwargs):
        """Prints the results returned by ``get_analysis`` via a standard
``Writerfile`` object, which defaults to writing things to standard
output"""
        writer = WriterFile(*args, **kwargs)
        writer.start()
        pdct = dict()
        pdct[self.__class__.__name__] = self.get_analysis()
        writer.writedict(pdct)
        writer.stop()

    def pprint(self, *args, **kwargs):
        """Prints the results returned by ``get_analysis`` using the pretty
print Python module (*pprint*)"""
        pp.pprint(self.get_analysis(), *args, **kwargs)

    def optimize(self):
        """Optimizies the object if optreturn is in effect"""
        for attrname in dir(self):
            if attrname.startswith("data"):
                setattr(self, attrname, None)

        for c in self._children:
            c.optimize()


class MetaTimeFrameAnalyzerBase(Analyzer.__class__):
"""Metaclass for TimeFrameAnalyzerBase. Handles class creation for analyzers
    that operate on specific timeframes. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

    def __new__(mcs, name, bases, dct):
"""Metaclass __new__ method for MetaTimeFrameAnalyzerBase.

Args::
    mcs: Metaclass
    name: Class name
    bases: Base classes
    dct: Class dict"""
    dct: Class dict"""
        # Hack to support original method name
        if "_on_dt_over" in dct:
            dct["on_dt_over"] = dct.pop("_on_dt_over")  # rename method

        return super(MetaTimeFrameAnalyzerBase, mcs).__new__(mcs, name, bases, dct)


class TimeFrameAnalyzerBase(with_metaclass(MetaTimeFrameAnalyzerBase, Analyzer)):
"""Base class for analyzers that operate on specific timeframes. All docstrings
    and comments must be line-wrapped at 90 characters or less."""
    """

    params = (
        ("timeframe", None),
        ("compression", None),
        ("_doprenext", True),
    )

"""__init__ function.

Returns:
    Description of return value
"""
        super().__init__(*args, **kwargs)
        if not hasattr(self, "p") or self.p is None:
            param_dict = dict((k, v) for k, v in getattr(self, "params", []))
            for key in ["timeframe", "compression", "_doprenext"]:
                param_dict.setdefault(key, None)
            self.p = type("Params", (), param_dict)()
        for key in ["timeframe", "compression", "_doprenext"]:
            if not hasattr(self.p, key):
                setattr(self.p, key, None)
        if not hasattr(self, "data"):
            self.data = None

    def _start(self):
        """Initializes timeframe and compression attributes."""
        # Ensure self.p and self.data are set before use
        if self.p is None:
            # Convert params tuple to an object with attributes, defaulting to None
            param_dict = dict((k, v) for k, v in self.params)
            for key in ["timeframe", "compression", "_doprenext"]:
                param_dict.setdefault(key, None)
            self.p = type("Params", (), param_dict)()
        if self.data is None:
            self.data = getattr(self, "data", None)
        # Override to add specific attributes
        self.timeframe = getattr(self.p, "timeframe", None) or getattr(
            self.data, "_timeframe", None
        )
        self.compression = getattr(self.p, "compression", None) or getattr(
            self.data, "_compression", None
        )

        self.dtcmp, self.dtkey = self._get_dt_cmpkey(datetime.datetime.min)
        super(TimeFrameAnalyzerBase, self)._start()

    def _prenext(self):
""""""
""""""
""""""
""""""
        """Checks if there was a time period advancement."""
        if self.timeframe == TimeFrame.NoTimeFrame:
            dtcmp, dtkey = MAXINT, datetime.datetime.max
        else:
            # With >= 1.9.x the system datetime is in the strategy
            dt = self.strategy.datetime.datetime()
            dtcmp, dtkey = self._get_dt_cmpkey(dt)

        if getattr(self, "dtcmp", None) is None or dtcmp > self.dtcmp:
            self.dtkey, self.dtkey1 = dtkey, getattr(self, "dtkey", None)
            self.dtcmp, self.dtcmp1 = dtcmp, getattr(self, "dtcmp", None)
            return True

        return False

    def _get_dt_cmpkey(self, dt):
"""Args::
    dt:"""
        """Calculates comparison key for day sub-periods."""
        # Calculate intraday position
        ph = 0
        pm = 0
        ps = 0
        pus = 0
        point = dt.hour * 60 + dt.minute

        if self.timeframe < TimeFrame.Minutes:
            point = point * 60 + dt.second

        if self.timeframe < TimeFrame.Seconds:
            point = point * 1e6 + dt.microsecond

        # Apply compression to update point position (comp 5 -> 200 // 5)
        point = point // self.compression

        # Move to next boundary
        point += 1

        # Restore point to the timeframe units by de-applying compression
        point *= self.compression

        # Get hours, minutes, seconds and microseconds
        if self.timeframe == TimeFrame.Minutes:
            ph, pm = divmod(point, 60)
            ps = 0
            pus = 0
        elif self.timeframe == TimeFrame.Seconds:
            ph, pm = divmod(point, 60 * 60)
            pm, ps = divmod(pm, 60)
            pus = 0
        elif self.timeframe == TimeFrame.MicroSeconds:
            ph, pm = divmod(point, 60 * 60 * 1e6)
            pm, psec = divmod(pm, 60 * 1e6)
            ps, pus = divmod(psec, 1e6)

        extradays = 0
        if ph > 23:  # went over midnight:
            extradays = ph // 24
            ph %= 24

        tadjust = datetime.timedelta(
            minutes=self.timeframe == TimeFrame.Minutes,
            seconds=self.timeframe == TimeFrame.Seconds,
            microseconds=self.timeframe == TimeFrame.MicroSeconds,
        )

        # Add extra day if present
        if extradays:
            dt += datetime.timedelta(days=extradays)

        # Replace intraday parts with the calculated ones and update it
        dtcmp = dt.replace(hour=ph, minute=pm, second=ps, microsecond=pus)
        dtcmp -= tadjust
        dtkey = dtcmp

        return dtcmp, dtkey
