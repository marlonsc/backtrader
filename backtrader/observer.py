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
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from .lineiterator import LineIterator, ObserverBase, StrategyBase
from .utils.py3 import with_metaclass


class MetaObserver(type):
    """Metaclass for ObserverBase to handle instantiation and pre-initialization."""

    def __new__(mcs, name, bases, dct):
        return super().__new__(mcs, name, bases, dct)

    def donew(cls, *args, **kwargs):
        """
        Instantiates a new Observer object and initializes analyzers list.

        :param *args:
        :param **kwargs:
        :return: tuple of (object, args, kwargs)
        """
        _obj = object.__new__(cls)
        _obj._analyzers = list()  # keep children analyzers
        return _obj, args, kwargs

    def dopreinit(cls, _obj, *args, **kwargs):
        """
        Pre-initialization for Observer, sets clock if strategy-wide observer.

        :param _obj:
        :param *args:
        :param **kwargs:
        :return: tuple of (object, args, kwargs)
        """
        # No super().dopreinit, as base type does not have it
        if getattr(_obj, "_stclock", False):
            _obj._clock = _obj._owner
        return _obj, args, kwargs


class Observer(with_metaclass(MetaObserver, ObserverBase)):
    """ """

    _stclock = False

    _OwnerCls = StrategyBase
    _ltype = LineIterator.ObsType

    csv = True

    plotinfo = dict(plot=False, subplot=True)

    # An Observer is ideally always observing and that' why prenext calls
    # next. The behaviour can be overriden by subclasses
    def prenext(self):
        """ """
        self.next()

    def _register_analyzer(self, analyzer):
        """

        :param analyzer:

        """
        self._analyzers.append(analyzer)

    def _start(self):
        """ """
        self.start()

    def start(self):
        """ """
