"""lineiterator.py module.

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
import collections.abc
import sys

from .dataseries import DataSeries
from .linebuffer import LineActions, LineNum
from .lineroot import LineRoot, LineSingle
from .lineseries import LineSeries, LineSeriesMaker

try:
    from backtrader.utils.dotdict import DotDict
except ImportError:
    # Fallback: minimal DotDict implementation
    class DotDict(dict):
        """Minimal DotDict fallback for linter compatibility."""

"""__getattr__ function.

Args:
    name: Description of name

Returns:
    Description of return value
"""
            return self[name]

"""__setattr__ function.

Args:
    name: Description of name
    value: Description of value

Returns:
    Description of return value
"""
            self[name] = value


from .utils.py3 import range, string_types, with_metaclass, zip


class MetaLineIterator(LineSeries.__class__):
"""Metaclass for LineIterator, manages instantiation and data binding for
    line-based objects. All docstrings and comments must be line-wrapped at
    90 characters or less."""
    """

    def donew(cls, *args, **kwargs):
        """"""
        _obj, args, kwargs = super(MetaLineIterator, cls).donew(*args, **kwargs)

        # Prepare to hold children that need to be calculated and
        # influence minperiod - Moved here to support LineNum below
        _obj._lineiterators = collections.defaultdict(list)

        # Scan args for datas ... if none are found,
        # use the _owner (to have a clock)
        mindatas = _obj._mindatas
        lastarg = 0
        _obj.datas = []
        for arg in args:
            if isinstance(arg, LineRoot):
                _obj.datas.append(LineSeriesMaker(arg))

            elif not mindatas:
                break  # found not data and must not be collected
            else:
                try:
                    _obj.datas.append(LineSeriesMaker(LineNum(arg)))
                except BaseException:
                    # Not a LineNum and is not a LineSeries - bail out
                    break

            mindatas = max(0, mindatas - 1)
            lastarg += 1

        newargs = args[lastarg:]

        # If no datas have been passed to an indicator ... use the
        # main datas of the owner, easing up adding "self.data" ...
        # if not _obj.datas and isinstance(_obj, (IndicatorBase, ObserverBase)):
        #     _obj.datas = _obj._owner.datas[0:mindatas]
        if not _obj.datas and isinstance(_obj, (IndicatorBase, ObserverBase)):
            # _obj.datas = _obj._owner.datas[0:mindatas]
            _obj.datas = _obj._owner.datas

        # Create a dictionary to be able to check for presence
        # lists in python use "==" operator when testing for presence with "in"
        # which doesn't really check for presence but for equality
        _obj.ddatas = {x: None for x in _obj.datas}

        # For each found data add access member -
        # for the first data 2 (data and data0)
        # #这一段可以优化，第一个for可以包含在第二个for中，第二个for当d = 0就是第一个for执行的内容
        if _obj.datas:
            _obj.data = data = _obj.datas[0]

            for l, line in enumerate(data.lines):
                linealias = data._getlinealias(l)
                if linealias:
                    setattr(_obj, "data_%s" % linealias, line)
                setattr(_obj, "data_%d" % l, line)

            for d, data in enumerate(_obj.datas):
                setattr(_obj, "data%d" % d, data)

                for l, line in enumerate(data.lines):
                    linealias = data._getlinealias(l)
                    if linealias:
                        setattr(_obj, "data%d_%s" % (d, linealias), line)
                    setattr(_obj, "data%d_%d" % (d, l), line)

        # Parameter values have now been set before __init__
        _obj.dnames = DotDict(
            [(d._name, d) for d in _obj.datas if getattr(d, "_name", "")]
        )

        return _obj, newargs, kwargs

    def dopreinit(cls, _obj, *args, **kwargs):
"""Pre-initialization logic for MetaLineIterator. Ensures datas and clock are set."""
        """
        # Only call super if it exists
        if hasattr(super(MetaLineIterator, cls), "dopreinit"):
            _obj, args, kwargs = super(MetaLineIterator, cls).dopreinit(
                _obj, *args, **kwargs
            )
        # if no datas were found use, use the _owner (to have a clock)
        _obj.datas = _obj.datas or [_obj._owner]
        # 1st data source is our ticking clock
        _obj._clock = _obj.datas[0]
        # To automatically set the period Start by scanning the found datas
        # No calculation can take place until all datas have yielded "data"
        # A data could be an indicator and it could take x bars until
        # something is produced
        _obj._minperiod = max([x._minperiod for x in _obj.datas] or [_obj._minperiod])
        # The lines carry at least the same minperiod as
        # that provided by the datas
        for line in _obj.lines:
            line.addminperiod(_obj._minperiod)
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
"""Post-initialization logic for MetaLineIterator. Ensures minperiod and registration."""
        """
        # Only call super if it exists
        if hasattr(super(MetaLineIterator, cls), "dopostinit"):
            _obj, args, kwargs = super(MetaLineIterator, cls).dopostinit(
                _obj, *args, **kwargs
            )
        # my minperiod is as large as the minperiod of my lines
        _obj._minperiod = max([x._minperiod for x in _obj.lines])
        # Recalc the period
        _obj._periodrecalc()
        # Register (my)self as indicator to owner once
        # _minperiod has been calculated
        if _obj._owner is not None:
            _obj._owner.addindicator(_obj)
        return _obj, args, kwargs


class LineIterator(with_metaclass(MetaLineIterator, LineSeries)):
"""Base class for all line-based iterators (Indicators, Observers, Strategies).
    Handles data binding, minperiod calculation, and orchestration of line
    operations. All docstrings and comments must be line-wrapped at 90 characters
    or less."""
    """

    _nextforce = False  # force cerebro to run in next mode (runonce=False)

    _mindatas = 1
    _ltype = LineSeries.IndType

    plotinfo = dict(
        plot=True,
        subplot=True,
        plotname="",
        plotskip=False,
        plotabove=False,
        plotlinelabels=False,
        plotlinevalues=True,
        plotvaluetags=True,
        plotymargin=0.0,
        plotyhlines=[],
        plotyticks=[],
        plothlines=[],
        plotforce=False,
        plotmaster=None,
        plotid=None,
        plotaspectratio=None,
        tradingdomain=None,
    )

    def _periodrecalc(self):
""""""
""""""
""""""
""""""
""""""
""""""
"""Args::
    indicator:"""
"""Args::
    owner: (Default value = None)
    own: (Default value = None)"""
    own: (Default value = None)"""
        if not owner:
            owner = 0

        if isinstance(owner, string_types):
            owner = [owner]
        elif not isinstance(owner, collections.abc.Iterable):
            owner = [owner]

        if not own:
            own = range(len(owner))

        if isinstance(own, string_types):
            own = [own]
        elif not isinstance(own, collections.abc.Iterable):
            own = [own]

        for lineowner, lineown in zip(owner, own):
            if isinstance(lineowner, string_types):
                lownerref = getattr(self._owner.lines, lineowner)
            else:
                lownerref = self._owner.lines[lineowner]

            if isinstance(lineown, string_types):
                lownref = getattr(self.lines, lineown)
            else:
                lownref = self.lines[lineown]

            lownref.addbinding(lownerref)

        return self

    # Alias which may be more readable
    bind2lines = bindlines
    bind2line = bind2lines

    def _next(self):
""""""
""""""
""""""
"""Args::
    start: 
    end:"""
    end:"""

    def oncestart(self, start, end):
"""Args::
    start: 
    end:"""
    end:"""
        self.once(start, end)

    def once(self, start, end):
"""Args::
    start: 
    end:"""
    end:"""

    def prenext(self):
"""This method will be called before the minimum period of all
        datas/indicators have been meet for the strategy to start executing"""
        """

    def nextstart(self):
"""This method will be called once, exactly when the minimum period for
        all datas/indicators have been meet. The default behavior is to call
        next"""
        """

        # Called once for 1st full calculation - defaults to regular next
        self.next()

    def next(self):
"""This method will be called for all remaining data points when the
        minimum period for all datas/indicators have been meet."""
        """

    def _addnotification(self, *args, **kwargs):
        """"""

    def _notify(self):
""""""
""""""
"""Args::
    savemem: (Default value = 0)"""
""""""
""""""
""""""
""""""
""""""
"""Args::
    cdata: 
    clock: (Default value = None)"""
    clock: (Default value = None)"""
        super(SingleCoupler, self).__init__()
        # _owner may not exist if not set by metaclass; fallback to None
        self._clock = clock if clock is not None else getattr(self, "_owner", None)

        self.cdata = cdata
        self.dlen = 0
        self.val = float("NaN")

    def next(self):
""""""
""""""
""""""
""""""
"""Args::
    cdata: 
    clock: (Default value = None)"""
    clock: (Default value = None)"""
    if isinstance(cdata, LineSingle):
        return SingleCoupler(cdata, clock)  # return for single line

    cdatacls = cdata.__class__  # copy important structures before creation
    try:
        LinesCoupler.counter += 1  # counter for unique class name
    except AttributeError:
        LinesCoupler.counter = 0

    # Prepare a MultiCoupler subclass
    nclsname = str("LinesCoupler_%d" % LinesCoupler.counter)
    ncls = type(nclsname, (MultiCoupler,), {})
    thismod = sys.modules[LinesCoupler.__module__]
    setattr(thismod, ncls.__name__, ncls)
    # Replace lines et al., to get a sensible clone
    ncls.lines = cdatacls.lines
    ncls.params = cdatacls.params
    ncls.plotinfo = cdatacls.plotinfo
    ncls.plotlines = cdatacls.plotlines

    # Ensure correct instantiation: pass only keyword arguments if needed
    try:
        obj = ncls(**kwargs)
    except TypeError:
        obj = ncls()
    # The clock is set here to avoid it being interpreted as a data by the
    # LineIterator background scanning code
    if clock is None:
        clock = getattr(cdata, "_clock", None)
        if clock is not None:
            nclock = getattr(clock, "_clock", None)
            if nclock is not None:
                clock = nclock
            else:
                nclock = getattr(clock, "data", None)
                if nclock is not None:
                    clock = nclock

        if clock is None:
            clock = obj._owner

    obj._clock = clock
    return obj


# Add an alias (which seems a lot more sensible for "Single Line" lines
LineCoupler = LinesCoupler
