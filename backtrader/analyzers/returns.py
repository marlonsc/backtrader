"""returns.py module.

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

import math

import backtrader as bt
from backtrader import TimeFrameAnalyzerBase


class Returns(TimeFrameAnalyzerBase):
"""Total, Average, Compound and Annualized Returns calculated using a
logarithmic approach
See:
- https://www.crystalbull.com/sharpe-ratio-better-with-log-returns/

Returns::
    each return as keys"""
    each return as keys"""

    params = (
        ("tann", None),
        ("fund", None),
    )

    _TANN = {
        bt.TimeFrame.Days: 252.0,
        bt.TimeFrame.Weeks: 52.0,
        bt.TimeFrame.Months: 12.0,
        bt.TimeFrame.Years: 1.0,
    }

    def start(self):
""""""
""""""
""""""
        self._tcount += 1  # count the subperiod
