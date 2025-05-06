#!/usr/bin389/env python
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
import itertools

from .cerebro import (
    Cerebro,  # If not present, define a stub or import correctly
)
from .metabase import ItemCollection, findowner

try:
    from .sizers import FixedSize
except ImportError:

    class FixedSize:
        pass


try:
    from .order import Order
except ImportError:

    class Order:
        pass


try:
    from .lineroot import LineRoot
except ImportError:

    class LineRoot:
        pass


try:
    from .signal import (
        SIGNAL_LONG,
        SIGNAL_LONG_ANY,
        SIGNAL_LONG_INV,
        SIGNAL_LONGEXIT,
        SIGNAL_LONGEXIT_ANY,
        SIGNAL_LONGEXIT_INV,
        SIGNAL_LONGSHORT,
        SIGNAL_NONE,
        SIGNAL_SHORT,
        SIGNAL_SHORT_ANY,
        SIGNAL_SHORT_INV,
        SIGNAL_SHORTEXIT,
        SIGNAL_SHORTEXIT_ANY,
        SIGNAL_SHORTEXIT_INV,
    )
except ImportError:
    SIGNAL_NONE = 0
    SIGNAL_LONGSHORT = 1
    SIGNAL_LONG = 2
    SIGNAL_LONG_INV = 3
    SIGNAL_LONG_ANY = 4
    SIGNAL_SHORT = 5
    SIGNAL_SHORT_INV = 6
    SIGNAL_SHORT_ANY = 7
    SIGNAL_LONGEXIT = 8
    SIGNAL_LONGEXIT_INV = 9
    SIGNAL_LONGEXIT_ANY = 10
    SIGNAL_SHORTEXIT = 11
    SIGNAL_SHORTEXIT_INV = 12
    SIGNAL_SHORTEXIT_ANY = 13
try:
    from .strategy import Strategy
except ImportError:

    class Strategy:
        pass


try:
    from .utils import AutoDictList, AutoOrderedDict
except ImportError:

    class AutoDictList(dict):
        pass

    class AutoOrderedDict(dict):
        pass


class MetaStrategy(type):
    """Metaclass for strategies."""

    _indcol = dict()

    def __new__(meta, name, bases, dct):
        """

        :param meta:
        :param name:
        :param bases:
        :param dct:

        """
        # Hack to support original method name for notify_order
        if "notify" in dct:
            # rename 'notify' to 'notify_order'
            dct["notify_order"] = dct.pop("notify")
        if "notify_operation" in dct:
            # rename 'notify' to 'notify_order'
            dct["notify_trade"] = dct.pop("notify_operation")

        return super(MetaStrategy, meta).__new__(meta, name, bases, dct)

    def __init__(cls, name, bases, dct):
        """Class has already been created ... register subclasses

        :param name:
        :param bases:
        :param dct:

        """
        # Initialize the class
        super(MetaStrategy, cls).__init__(name, bases, dct)

        if (
            not getattr(cls, "aliased", False)
            and name != "Strategy"
            and not name.startswith("_")
        ):
            cls._indcol[name] = cls

    def donew(self, *args, **kwargs):
        """

        :param *args:
        :param **kwargs:

        """
        # Only call super if it exists
        if hasattr(super(MetaStrategy, self), "donew"):
            _obj, args, kwargs = super(MetaStrategy, self).donew(*args, **kwargs)
        else:
            _obj = object.__new__(self)
        # Find the owner and store it
        _obj.env = _obj.cerebro = cerebro = findowner(_obj, Cerebro)
        _obj._id = getattr(cerebro, "_next_stid", lambda: 0)()
        return _obj, args, kwargs

    def dopreinit(self, _obj, *args, **kwargs):
        """

        :param _obj:
        :param *args:
        :param **kwargs:

        """
        if hasattr(super(MetaStrategy, self), "dopreinit"):
            _obj, args, kwargs = super(MetaStrategy, self).dopreinit(
                _obj, *args, **kwargs
            )
        _obj.broker = getattr(_obj.env, "broker", None)
        _obj._sizer = FixedSize()
        _obj._orders = list()
        _obj._orderspending = list()
        _obj._trades = collections.defaultdict(AutoDictList)
        _obj._tradespending = list()
        _obj.stats = _obj.observers = ItemCollection()
        _obj.analyzers = ItemCollection()
        _obj._alnames = collections.defaultdict(itertools.count)
        _obj.writers = list()
        _obj._slave_analyzers = list()
        _obj._tradehistoryon = False
        return _obj, args, kwargs

    def dopostinit(self, _obj, *args, **kwargs):
        """

        :param _obj:
        :param *args:
        :param **kwargs:

        """
        if hasattr(super(MetaStrategy, self), "dopostinit"):
            _obj, args, kwargs = super(MetaStrategy, self).dopostinit(
                _obj, *args, **kwargs
            )
        _obj._sizer.set(_obj, getattr(_obj, "broker", None))
        return _obj, args, kwargs
