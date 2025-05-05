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

import itertools
import sys

PY2 = sys.version_info.major == 2

if PY2:
    try:
        import _winreg as winreg
    except ImportError:
        winreg = None

    MAXINT = sys.maxint
    MININT = -sys.maxint - 1

    MAXFLOAT = sys.float_info.max
    MINFLOAT = sys.float_info.min

    string_types = str, unicode
    integer_types = int, long

    filter = itertools.ifilter
    map = itertools.imap
    range = xrange
    zip = itertools.izip
    long = long

    cmp = cmp

    bytes = bytes
    bstr = bytes

    def iterkeys(d):
        """

        :param d:

        """
        return d.iterkeys()

    def itervalues(d):
        """

        :param d:

        """
        return d.itervalues()

    def iteritems(d):
        """

        :param d:

        """
        return d.iteritems()

    def keys(d):
        """

        :param d:

        """
        return d.keys()

    def values(d):
        """

        :param d:

        """
        return d.values()

    def items(d):
        """

        :param d:

        """
        return d.items()

else:
    try:
        import winreg
    except ImportError:
        winreg = None

    MAXINT = sys.maxsize
    MININT = -sys.maxsize - 1

    MAXFLOAT = sys.float_info.max
    MINFLOAT = sys.float_info.min

    string_types = (str,)
    integer_types = (int,)

    filter = filter
    map = map
    range = range
    zip = zip
    long = int

    def cmp(a, b):
        """

        :param a:
        :param b:

        """
        return (a > b) - (a < b)

    def bytes(x):
        """

        :param x:

        """
        return x.encode("utf-8")

    def bstr(x):
        """

        :param x:

        """
        return str(x)

    def iterkeys(d):
        """

        :param d:

        """
        return iter(d.keys())

    def itervalues(d):
        """

        :param d:

        """
        return iter(d.values())

    def iteritems(d):
        """

        :param d:

        """
        return iter(d.items())

    def keys(d):
        """

        :param d:

        """
        return list(d.keys())

    def values(d):
        """

        :param d:

        """
        return list(d.values())

    def items(d):
        """

        :param d:

        """
        return list(d.items())


# This is from Armin Ronacher from Flash simplified later by six
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass.

    :param meta:
    :param *bases:

    """

    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):
        """ """

        def __new__(cls, name, this_bases, d):
            """

            :param name:
            :param this_bases:
            :param d:

            """
            return meta(name, bases, d)

    return type.__new__(metaclass, str("temporary_class"), (), {})
