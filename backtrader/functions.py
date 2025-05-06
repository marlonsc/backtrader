"""functions.py module.

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

import functools
import math

from .linebuffer import LineActions
from .utils.py3 import cmp, range


# Generate a List equivalent which uses "is" for contains
class List(list):
"""List subclass using 'is' for contains. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

    def __contains__(self, other):
"""Args::
    other:"""
"""Base class for logic operations on line objects. All docstrings and comments
    must be line-wrapped at 90 characters or less."""
    """

    def __init__(self, *args):
        """"""
        super(Logic, self).__init__()
        self.args = [self.arrayize(arg) for arg in args]


class DivByZero(Logic):
"""This operation is a Lines object and fills it values by executing a
    division on the numerator / denominator arguments and avoiding a division
    by zero exception by checking the denominator"""
    """

    def __init__(self, a, b, zero=0.0):
"""Args::
    a: 
    b: 
    zero: (Default value = 0.0)"""
    zero: (Default value = 0.0)"""
        super(DivByZero, self).__init__(a, b)
        self.a = a
        self.b = b
        self.zero = zero

    def next(self):
""""""
"""Args::
    start: 
    end:"""
    end:"""
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array
        zero = self.zero

        for i in range(start, end):
            b = srcb[i]
            dst[i] = srca[i] / b if b else zero


class DivZeroByZero(Logic):
"""This operation is a Lines object and fills it values by executing a
    division on the numerator / denominator arguments and avoiding a division
    by zero exception or an indetermination by checking the
    denominator/numerator pair"""
    """

    def __init__(self, a, b, single=float("inf"), dual=0.0):
"""Args::
    a: 
    b: 
    single: (Default value = float("inf"))
    dual: (Default value = 0.0)"""
    dual: (Default value = 0.0)"""
        super(DivZeroByZero, self).__init__(a, b)
        self.a = a
        self.b = b
        self.single = single
        self.dual = dual

    def next(self):
""""""
"""Args::
    start: 
    end:"""
    end:"""
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array
        single = self.single
        dual = self.dual

        for i in range(start, end):
            b = srcb[i]
            a = srca[i]
            if b == 0.0:
                dst[i] = dual if a == 0.0 else single
            else:
                dst[i] = a / b


class Cmp(Logic):
"""Compares two line objects element-wise. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

    def __init__(self, a, b):
"""Args::
    a: 
    b:"""
    b:"""
        super(Cmp, self).__init__(a, b)
        self.a = self.args[0]
        self.b = self.args[1]

    def next(self):
""""""
"""Args::
    start: 
    end:"""
    end:"""
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array

        for i in range(start, end):
            dst[i] = cmp(srca[i], srcb[i])


class CmpEx(Logic):
"""Extended comparison logic for line objects. All docstrings and comments must
    be line-wrapped at 90 characters or less."""
    """

    def __init__(self, a, b, r1, r2, r3):
"""Args::
    a: 
    b: 
    r1: 
    r2: 
    r3:"""
    r3:"""
        super(CmpEx, self).__init__(a, b, r1, r2, r3)
        self.a = self.args[0]
        self.b = self.args[1]
        self.r1 = self.args[2]
        self.r2 = self.args[3]
        self.r3 = self.args[4]

    def next(self):
""""""
"""Args::
    start: 
    end:"""
    end:"""
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array
        r1 = self.r1.array
        r2 = self.r2.array
        r3 = self.r3.array

        for i in range(start, end):
            ai = srca[i]
            bi = srcb[i]

            if ai < bi:
                dst[i] = r1[i]
            elif ai > bi:
                dst[i] = r3[i]
            else:
                dst[i] = r2[i]


class If(Logic):
"""Implements conditional logic for line objects. All docstrings and comments
    must be line-wrapped at 90 characters or less."""
    """

    def __init__(self, cond, a, b):
"""Args::
    cond: 
    a: 
    b:"""
    b:"""
        super(If, self).__init__(a, b)
        self.a = self.args[0]
        self.b = self.args[1]
        self.cond = self.arrayize(cond)

    def next(self):
""""""
"""Args::
    start: 
    end:"""
    end:"""
        # cache python dictionary lookups
        dst = self.array
        srca = self.a.array
        srcb = self.b.array
        cond = self.cond.array

        for i in range(start, end):
            dst[i] = srca[i] if cond[i] else srcb[i]


class MultiLogic(Logic):
"""Base class for multi-argument logic operations. All docstrings and comments
    must be line-wrapped at 90 characters or less."""
    """

    flogic = None

    def next(self):
""""""
"""Args::
    start: 
    end:"""
    end:"""
        # cache python dictionary lookups
        dst = self.array
        arrays = [arg.array for arg in self.args]
        flogic = type(self).flogic
        if flogic is None or not callable(flogic):
            raise NotImplementedError(
                "flogic must be defined in subclass and callable."
            )
        for i in range(start, end):
            dst[i] = flogic(*[arr[i] for arr in arrays])


class SingleLogic(Logic):
"""Base class for single-argument logic operations. All docstrings and comments
    must be line-wrapped at 90 characters or less."""
    """

    flogic = None

    def next(self):
""""""
"""Args::
    start: 
    end:"""
    end:"""
        # cache python dictionary lookups
        dst = self.array
        flogic = type(self).flogic
        if flogic is None or not callable(flogic):
            raise NotImplementedError(
                "flogic must be defined in subclass and callable."
            )
        for i in range(start, end):
            dst[i] = flogic(self.args[0].array[i])


class MultiLogicReduce(MultiLogic):
"""Base class for multi-argument logic operations with reduction. All docstrings
    and comments must be line-wrapped at 90 characters or less."""
    """

    def __init__(self, *args, **kwargs):
        """"""
        super(MultiLogicReduce, self).__init__(*args)
        if "initializer" not in kwargs:
            self.flogic = lambda *a: functools.reduce(type(self).flogic, a)
        else:
            self.flogic = lambda *a: functools.reduce(
                type(self).flogic, a, kwargs["initializer"]
            )


class Reduce(MultiLogicReduce):
"""Reduces multiple arguments using a specified logic function. All docstrings
    and comments must be line-wrapped at 90 characters or less."""
    """

    def __init__(self, flogic, *args, **kwargs):
"""Args::
    flogic:"""
"""Args::
    x: 
    y:"""
    y:"""
    return bool(x and y)


class And(MultiLogicReduce):
"""Logical AND reduction for multiple arguments. All docstrings and comments must
    be line-wrapped at 90 characters or less."""
    """

    flogic = _andlogic


def _orlogic(x, y):
"""Args::
    x: 
    y:"""
    y:"""
    return bool(x or y)


class Or(MultiLogicReduce):
"""Logical OR reduction for multiple arguments. All docstrings and comments must
    be line-wrapped at 90 characters or less."""
    """

    flogic = _orlogic


"""_maxlogic function.

Returns:
    Description of return value
"""
    return max(args)


"""_minlogic function.

Returns:
    Description of return value
"""
    return min(args)


"""_sumlogic function.

Returns:
    Description of return value
"""
    return math.fsum(args)


"""_anylogic function.

Returns:
    Description of return value
"""
    return any(args)


"""_alllogic function.

Returns:
    Description of return value
"""
    return all(args)


class Max(MultiLogic):
"""Element-wise maximum for multiple arguments. All docstrings and comments must
    be line-wrapped at 90 characters or less."""
    """

    flogic = _maxlogic


class Min(MultiLogic):
"""Element-wise minimum for multiple arguments. All docstrings and comments must
    be line-wrapped at 90 characters or less."""
    """

    flogic = _minlogic


class Sum(MultiLogic):
"""Element-wise sum for multiple arguments. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

    flogic = _sumlogic


class Any(MultiLogic):
"""Element-wise any() for multiple arguments. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

    flogic = _anylogic


class All(MultiLogic):
"""Element-wise all() for multiple arguments. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

    flogic = _alllogic


class Log(SingleLogic):
"""Element-wise log10 for a single argument. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

    flogic = math.log10


class Ceiling(SingleLogic):
"""Element-wise ceiling for a single argument. All docstrings and comments must
    be line-wrapped at 90 characters or less."""
    """

    flogic = math.ceil


class Floor(SingleLogic):
"""Element-wise floor for a single argument. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

    flogic = math.floor


class Abs(SingleLogic):
"""Element-wise absolute value for a single argument. All docstrings and comments
    must be line-wrapped at 90 characters or less."""
    """

    flogic = math.fabs
