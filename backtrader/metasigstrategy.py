"""metasigstrategy.py module.

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

try:
    from .utils import AutoDictList, AutoOrderedDict
except ImportError:

"""AutoDictList class.

Description of the class functionality."""
        pass

"""AutoOrderedDict class.

Description of the class functionality."""
        pass


try:
    from .sizers import FixedSize
except ImportError:

"""FixedSize class.

Description of the class functionality."""
        pass


try:
    from .order import Order
except ImportError:

"""Order class.

Description of the class functionality."""
        pass


try:
    from .lineroot import LineRoot
except ImportError:

"""LineRoot class.

Description of the class functionality."""
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

"""Strategy class.

Description of the class functionality."""
        pass


try:
    from .utils.py3 import integer_types, string_types
except ImportError:
    integer_types = (int,)
    string_types = (str,)


class MetaSigStrategy(type):
    """Metaclass for signal strategies."""

    def __new__(meta, name, bases, dct):
"""Args::
    meta: 
    name: 
    bases: 
    dct:"""
    dct:"""
        # map user defined next to custom to be able to call own method before
        if "next" in dct:
            dct["_next_custom"] = dct.pop("next")

        cls = super(MetaSigStrategy, meta).__new__(meta, name, bases, dct)

        # after class creation remap _next_catch to be next if present
        if hasattr(cls, "_next_catch"):
            cls.next = cls._next_catch
        return cls

    def dopreinit(self, _obj, *args, **kwargs):
"""Args::
    _obj:"""
"""Args::
    _obj:"""
    _obj:"""
        if hasattr(super(MetaSigStrategy, self), "dopostinit"):
            _obj, args, kwargs = super(MetaSigStrategy, self).dopostinit(
                _obj, *args, **kwargs
            )
        for sigtype, sigcls, sigargs, sigkwargs in getattr(_obj.p, "signals", []):
            _obj._signals[sigtype].append(sigcls(*sigargs, **sigkwargs))
        # Record types of signals
        _obj._longshort = bool(_obj._signals[SIGNAL_LONGSHORT])
        _obj._long = bool(_obj._signals[SIGNAL_LONG])
        _obj._short = bool(_obj._signals[SIGNAL_SHORT])
        _obj._longexit = bool(_obj._signals[SIGNAL_LONGEXIT])
        _obj._shortexit = bool(_obj._signals[SIGNAL_SHORTEXIT])
        return _obj, args, kwargs
