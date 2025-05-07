"""timereturn.py module.

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

from backtrader import TimeFrameAnalyzerBase


class TimeReturn(TimeFrameAnalyzerBase):
"""This analyzer calculates the Returns by looking at the beginning
and end of the timeframe

Returns::
    each return as keys"""
    each return as keys"""

    params = (
        ("data", None),
        ("firstopen", True),
        ("fund", None),
    )

    def start(self):
""""""
"""Args::
    cash: 
    value: 
    fundvalue: 
    shares:"""
    shares:"""
        if not self._fundmode:
            # Record current value
            if self.p.data is None:
                self._value = value  # the portofolio value if tracking no data
            else:
                self._value = self.p.data[0]  # the data value if tracking data
        else:
            if self.p.data is None:
                self._value = fundvalue  # the fund value if tracking no data
            else:
                self._value = self.p.data[0]  # the data value if tracking data

    def on_dt_over(self):
""""""
""""""
        """Optimizies the object if optreturn is in effect"""
        super().optimize()

        self.strategy = None
