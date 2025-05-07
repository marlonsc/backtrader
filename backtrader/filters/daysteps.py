"""daysteps.py module.

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


class BarReplayer_Open(object):
    """This filters splits a bar in two parts:
- ``Open``: the opening price of the bar will be used to deliver an
initial price bar in which the four components (OHLC) are equal
The volume/openinterest fields are 0 for this initial bar
- ``OHLC``: the original bar is delivered complete with the original
``volume``/``openinterest``
The split simulates a replay without the need to use the *replay* filter."""

    def __init__(self, data):
"""Args::
    data:"""
"""Args::
    data:"""
"""Called when the data is no longer producing bars
Can be called multiple times. It has the chance to (for example)
produce extra bars

Args::
    data:"""
    data:"""
        if self.pendingbar is not None:
            data.backwards()  # remove delivered open bar
            data._add2stack(self.pendingbar)  # add remaining
            self.pendingbar = None  # No further action
            return True  # something delivered

        return False  # nothing delivered here


# Alias
DayStepsFilter = BarReplayer_Open
