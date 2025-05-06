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
""".. module:: lineroot
Definition of the base class LineRoot and base classes LineSingle/LineMultiple
to define interfaces and hierarchy for the real operational classes
.. moduleauthor:: Daniel Rodriguez"""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import operator

from . import metabase
from .utils.py3 import range, with_metaclass


class MetaLineRoot(metabase.MetaParams):
"""Metaclass for LineRoot. Handles owner resolution and pre-init logic for
    line root objects. All docstrings and comments must be line-wrapped at
    90 characters or less."""
    """

    def donew(cls, *args, **kwargs):
        """"""
        _obj, args, kwargs = super(MetaLineRoot, cls).donew(*args, **kwargs)

        # Find the owner and store it
        # startlevel = 4 ... to skip intermediate call stacks
        ownerskip = kwargs.pop("_ownerskip", None)
        _obj._owner = metabase.findowner(
            _obj, _obj._OwnerCls or LineMultiple, skip=ownerskip
        )

        # Parameter values have now been set before __init__
        return _obj, args, kwargs


class LineRoot(with_metaclass(MetaLineRoot, object)):
"""Defines a common base and interfaces for Single and Multiple LineXXX instances.
    Handles period management, iteration, and rich operator overloading for line
    objects. All docstrings and comments must be line-wrapped at 90 characters or
    less."""
    """

    _OwnerCls = None
    _minperiod = 1
    _opstage = 1

    IndType, StratType, ObsType = range(3)

    def _stage1(self):
""""""
""""""
"""Args::
    other: 
    operation: 
    r: (Default value = False)
    intify: (Default value = False)"""
    intify: (Default value = False)"""
        if self._opstage == 1:
            return self._operation_stage1(other, operation, r=r, intify=intify)

        return self._operation_stage2(other, operation, r=r)

    def _operationown(self, operation):
"""Args::
    operation:"""
"""Change the lines to implement a minimum size qbuffer scheme

Args::
    savemem: (Default value = 0)"""
    savemem: (Default value = 0)"""
        raise NotImplementedError

    def minbuffer(self, size):
"""Receive notification of how large the buffer must at least be

Args::
    size:"""
    size:"""
        raise NotImplementedError

    def setminperiod(self, minperiod):
"""Direct minperiod manipulation. It could be used for example
by a strategy
to not wait for all indicators to produce a value

Args::
    minperiod:"""
    minperiod:"""
        self._minperiod = minperiod

    def updateminperiod(self, minperiod):
"""Update the minperiod if needed. The minperiod will have been
calculated elsewhere
and has to take over if greater that self's

Args::
    minperiod:"""
    minperiod:"""
        self._minperiod = max(self._minperiod, minperiod)

    def addminperiod(self, minperiod):
"""Add a minperiod to own ... to be defined by subclasses

Args::
    minperiod:"""
    minperiod:"""
        raise NotImplementedError

    def incminperiod(self, minperiod):
"""Increment the minperiod with no considerations

Args::
    minperiod:"""
    minperiod:"""
        raise NotImplementedError

    def prenext(self):
        """It will be called during the "minperiod" phase of an iteration."""

    def nextstart(self):
"""It will be called when the minperiod phase is over for the 1st
        post-minperiod value. Only called once and defaults to automatically
        calling next"""
        """
        self.next()

    def next(self):
        """Called to calculate values when the minperiod is over"""

    def preonce(self, start, end):
"""It will be called during the "minperiod" phase of a "once" iteration

Args::
    start: 
    end:"""
    end:"""

    def oncestart(self, start, end):
"""It will be called when the minperiod phase is over for the 1st
post-minperiod value
Only called once and defaults to automatically calling once

Args::
    start: 
    end:"""
    end:"""
        self.once(start, end)

    def once(self, start, end):
"""Called to calculate values at "once" when the minperiod is over

Args::
    start: 
    end:"""
    end:"""

    # Arithmetic operators
    def _makeoperation(self, other, operation, r=False, _ownerskip=None):
"""Args::
    other: 
    operation: 
    r: (Default value = False)
    _ownerskip: (Default value = None)"""
    _ownerskip: (Default value = None)"""
        raise NotImplementedError

    def _makeoperationown(self, operation, _ownerskip=None):
"""Args::
    operation: 
    _ownerskip: (Default value = None)"""
    _ownerskip: (Default value = None)"""
        raise NotImplementedError

    def _operationown_stage1(self, operation):
"""Operation with single operand which is "self"

Args::
    operation:"""
    operation:"""
        return self._makeoperationown(operation, _ownerskip=self)

    def _roperation(self, other, operation, intify=False):
"""Relies on self._operation to and passes "r" True to define a
reverse operation

Args::
    other: 
    operation: 
    intify: (Default value = False)"""
    intify: (Default value = False)"""
        return self._operation(other, operation, r=True, intify=intify)

    def _operation_stage1(self, other, operation, r=False, intify=False):
"""Two operands' operation. Scanning of other happens to understand
if other must be directly an operand or rather a subitem thereof

Args::
    other: 
    operation: 
    r: (Default value = False)
    intify: (Default value = False)"""
    intify: (Default value = False)"""
        if isinstance(other, LineMultiple):
            other = other.lines[0]

        return self._makeoperation(other, operation, r, self)

    def _operation_stage2(self, other, operation, r=False):
"""Rich Comparison operators. Scans other and returns either an
operation with other directly or a subitem from other

Args::
    other: 
    operation: 
    r: (Default value = False)"""
    r: (Default value = False)"""
        if isinstance(other, LineRoot):
            other = other[0]

        # operation(float, other) ... expecting other to be a float
        if r:
            return operation(other, self[0])

        return operation(self[0], other)

    def _operationown_stage2(self, operation):
"""Args::
    operation:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
""""""
""""""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    other:"""
""""""
"""Represents multiple time series lines. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

    def reset(self):
"""Reset all lines in this LineMultiple instance."""
        """
        lines = getattr(self, "lines", None)
        if lines is not None:
            lines.reset()
        self._stage1()

    def _stage1(self):
"""Set stage 1 for all lines in this LineMultiple instance."""
        """
        lines = getattr(self, "lines", None)
        if lines is not None:
            lines._stage1()
        self._opstage = 1

    def _stage2(self):
"""Set stage 2 for all lines in this LineMultiple instance."""
        """
        lines = getattr(self, "lines", None)
        if lines is not None:
            lines._stage2()
        self._opstage = 2

    def addminperiod(self, minperiod):
"""Add minperiod to all lines in this LineMultiple instance."""
        """
        lines = getattr(self, "lines", None)
        if lines is not None:
            lines.addminperiod(minperiod)

    def incminperiod(self, minperiod):
"""Increment minperiod for all lines in this LineMultiple instance."""
        """
        lines = getattr(self, "lines", None)
        if lines is not None:
            lines.incminperiod(minperiod)

    def _makeoperation(self, other, operation, r=False, _ownerskip=None):
"""Make operation for all lines in this LineMultiple instance."""
        """
        lines = getattr(self, "lines", None)
        if lines is not None:
            return lines._makeoperation(other, operation, r, _ownerskip)
        raise AttributeError("No 'lines' attribute in LineMultiple instance")

    def _makeoperationown(self, operation, _ownerskip=None):
"""Make own operation for all lines in this LineMultiple instance."""
        """
        lines = getattr(self, "lines", None)
        if lines is not None:
            return lines._makeoperationown(operation, _ownerskip)
        raise AttributeError("No 'lines' attribute in LineMultiple instance")

    def qbuffer(self, savemem=0):
"""Enable memory saving scheme for all lines in this LineMultiple instance."""
        """
        lines = getattr(self, "lines", None)
        if lines is not None:
            lines.qbuffer(savemem)

    def minbuffer(self, size):
"""Set minimum buffer size for all lines in this LineMultiple instance."""
        """
        lines = getattr(self, "lines", None)
        if lines is not None:
            lines.minbuffer(size)


class LineSingle(LineRoot):
"""Represents a single time series line. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

    def addminperiod(self, minperiod):
"""Add the minperiod (substracting the overlapping 1 minimum period)

Args::
    minperiod:"""
    minperiod:"""
        self._minperiod += minperiod - 1

    def incminperiod(self, minperiod):
"""Increment the minperiod with no considerations

Args::
    minperiod:"""
    minperiod:"""
        self._minperiod += minperiod
