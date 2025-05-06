"""autodict.py module.

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

from collections import OrderedDict, defaultdict

from .py3 import values as py3lvalues


def Tree():
""""""
""""""
"""Args::
    key:"""
""""""
"""Args::
    key:"""
""""""
""""""
""""""
"""Args::
    key:"""
"""Args::
    key:"""
"""Args::
    key: 
    value:"""
    value:"""
        if False and key.startswith("_"):
            self.__dict__[key] = value
            return

        self[key] = value


class AutoOrderedDict(OrderedDict):
""""""
""""""
""""""
"""Args::
    key:"""
"""Args::
    key:"""
"""Args::
    key: 
    value:"""
    value:"""
        if key.startswith("_"):
            self.__dict__[key] = value
            return

        self[key] = value

    # Define math operations
    def __iadd__(self, other):
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
        return py3lvalues(self)
