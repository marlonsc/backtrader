#!/usr/bin/env python
"""This module contains utility functions for Python 3.
"""
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

import sys

MAXINT = sys.maxsize
MININT = -sys.maxsize - 1

MAXFLOAT = sys.float_info.max
MINFLOAT = sys.float_info.min

string_types = (str,)
integer_types = (int,)

long = int # pylint: disable=invalid-name

def cmp(a, b):
    """Args:
    a:
    b:"""
    return (a > b) - (a < b)

def bstr(x):
    """Convert x to a string.

    Args:
        x: The object to convert to a string.

    Returns:
        str: The string representation of x.
    """
    return str(x)

def iterkeys(d):
    """Iterate over the keys of d.

    Args:
        d: The dictionary to iterate over.

    Returns:
        iterator: An iterator over the keys of d.
    """
    return iter(d.keys())

def itervalues(d):
    """Iterate over the values of d.

    Args:
        d: The dictionary to iterate over.

    Returns:
        iterator: An iterator over the values of d.
    """
    return iter(d.values())

def iteritems(d):
    """Iterate over the items of d.

    Args:
        d: The dictionary to iterate over.

    Returns:
        iterator: An iterator over the items of d.
    """
    return iter(d.items())

def keys(d):
    """Get the keys of d.

    Args:
        d: The dictionary to get the keys of.

    Returns:
        list: A list of the keys of d.
    """
    return list(d.keys())

def values(d):
    """Get the values of d.

    Args:
        d: The dictionary to get the values of.

    Returns:
        list: A list of the values of d.
    """
    return list(d.values())

def items(d):
    """Get the items of d.

    Args:
        d: The dictionary to get the items of.

    Returns:
        list: A list of the items of d.
    """
    return list(d.items())

# This is from Armin Ronacher from Flash simplified later by six
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass.

    Args:
        meta: The metaclass to use.
        bases: The bases to use.

    Returns:
        type: A new base class with the metaclass.
    """

    class metaclass(meta): # pylint: disable=invalid-name
        """This requires a bit of explanation: the basic idea is to make a dummy
        metaclass for one level of class instantiation that replaces itself with
        the actual metaclass."""

        def __new__(cls, name, this_bases, d): # pylint: disable=unused-argument
            """Create a new base class with the metaclass.

            Args:
                name: The name of the new base class.
                this_bases: The bases to use.
                d: The dictionary to use.

            Returns:
                type: A new base class with the metaclass.
            """
            return meta(name, bases, d)

    return type.__new__(metaclass, str("temporary_class"), (), {})
