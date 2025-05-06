"""py3.py module.

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
"""Args::
    d:"""
"""Args::
    d:"""
"""Args::
    d:"""
"""Args::
    d:"""
"""Args::
    d:"""
"""Args::
    d:"""
"""Args::
    a: 
    b:"""
    b:"""
        return (a > b) - (a < b)

    def bytes(x):
"""Args::
    x:"""
"""Args::
    x:"""
"""Args::
    d:"""
"""Args::
    d:"""
"""Args::
    d:"""
"""Args::
    d:"""
"""Args::
    d:"""
"""Args::
    d:"""
"""Create a base class with a metaclass.

Args::
    meta:"""
    meta:"""

    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):
""""""
"""Args::
    name: 
    this_bases: 
    d:"""
    d:"""
            return meta(name, bases, d)

    return type.__new__(metaclass, str("temporary_class"), (), {})
