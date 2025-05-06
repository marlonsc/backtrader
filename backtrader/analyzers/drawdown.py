"""drawdown.py module.

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

import backtrader as bt
from backtrader.utils import AutoOrderedDict

__all__ = ["DrawDown", "TimeDrawDown"]


class DrawDown(bt.Analyzer):
"""This analyzer calculates trading system drawdowns stats such as drawdown
values in %s and in dollars, max drawdown in %s and in dollars, drawdown
length and drawdown max length

Returns::
    drawdown stats as values, the following keys/attributes are available:"""
    drawdown stats as values, the following keys/attributes are available:"""

    params = (("fund", None),)

    def start(self):
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
            self._value = value  # record current value
            self._maxvalue = max(self._maxvalue, value)  # update peak value
        else:
            self._value = fundvalue  # record current value
            self._maxvalue = max(self._maxvalue, fundvalue)  # update peak

    def next(self):
""""""
"""This analyzer calculates trading system drawdowns on the chosen
timeframe which can be different from the one used in the underlying data

Returns::
    drawdown stats as values, the following keys/attributes are available:"""
    drawdown stats as values, the following keys/attributes are available:"""

    params = (("fund", None),)

    def start(self):
""""""
""""""
""""""
        self.rets["maxdrawdown"] = round(self.maxdd, 2)
        self.rets["maxdrawdownperiod"] = self.maxddlen
