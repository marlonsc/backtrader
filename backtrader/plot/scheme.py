"""scheme.py module.

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

tableau20 = [
    "steelblue",  # 0
    "lightsteelblue",  # 1
    "darkorange",  # 2
    "peachpuff",  # 3
    "green",  # 4
    "lightgreen",  # 5
    "crimson",  # 6
    "lightcoral",  # 7
    "mediumpurple",  # 8
    "thistle",  # 9
    "saddlebrown",  # 10
    "rosybrown",  # 11
    "orchid",  # 12
    "lightpink",  # 13
    "gray",  # 14
    "lightgray",  # 15
    "olive",  # 16
    "palegoldenrod",  # 17
    "mediumturquoise",  # 18
    "paleturquoise",  # 19
]

tableau10 = [
    "blue",  # 'steelblue',  # 0
    "darkorange",  # 1
    "green",  # 2
    "crimson",  # 3
    "mediumpurple",  # 4
    "saddlebrown",  # 5
    "orchid",  # 6
    "gray",  # 7
    "olive",  # 8
    "mediumturquoise",  # 9
]

tableau10_light = [
    "lightsteelblue",  # 0
    "peachpuff",  # 1
    "lightgreen",  # 2
    "lightcoral",  # 3
    "thistle",  # 4
    "rosybrown",  # 5
    "lightpink",  # 6
    "lightgray",  # 7
    "palegoldenrod",  # 8
    "paleturquoise",  # 9
]

tab10_index = [3, 0, 2, 1, 2, 4, 5, 6, 7, 8, 9]


class PlotScheme(object):
""""""
""""""
"""Args::
    idx:"""
    idx:"""
        colidx = tab10_index[idx % len(tab10_index)]
        return self.lcolors[colidx]
