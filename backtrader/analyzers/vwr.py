"""vwr.py module.

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

from ..mathsupport import standarddev
from . import Returns


class VWR(TimeFrameAnalyzerBase):
"""Variability-Weighted Return: Better SharpeRatio with Log Returns
Alias:
- VariabilityWeightedReturn
See:
- https://www.crystalbull.com/sharpe-ratio-better-with-log-returns/

Returns::
    each return as keys"""
    each return as keys"""

    params = (
        ("timeframe", bt.TimeFrame.Days),  # Default to Days
        ("compression", None),
        ("tann", None),
        ("tau", 2.0),
        ("sdev_max", 0.3),
        ("fund", None),
        ("riskfreerate", 0.01),
        ("stddev_sample", False),
    )

    _TANN = {
        bt.TimeFrame.Days: 252.0,
        bt.TimeFrame.Weeks: 52.0,
        bt.TimeFrame.Months: 12.0,
        bt.TimeFrame.Years: 1.0,
    }

    def __init__(self):
""""""
""""""
""""""
"""Args::
    cash: 
    value: 
    fundvalue: 
    shares:"""
    shares:"""
        if not self._fundmode:
            self._pns[-1] = value  # Annotate last seen pn for current period
        else:
            self._pns[-1] = fundvalue  # Annotate last pn for current period

    def _on_dt_over(self):
""""""
        self._pis.append(self._pns[-1])  # Last pn is pi in next period
        self._pns.append(None)  # Placeholder for [-1] operation


VariabilityWeightedReturn = VWR
