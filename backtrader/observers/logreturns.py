"""logreturns.py module.

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

__all__ = ["LogReturns", "LogReturns2"]


class LogReturns(bt.Observer):
    """This observer stores the *log returns* of the strategy or a"""

    _stclock = True

    lines = ("logret1",)
    plotinfo = dict(plot=True, subplot=True)

    params = (
        ("timeframe", None),
        ("compression", None),
        ("fund", None),
    )

    def _plotlabel(self):
""""""
""""""
""""""
    """Extends the observer LogReturns to show two instruments"""

    lines = ("logret2",)

    def __init__(self):
""""""
""""""
        super(LogReturns2, self).next()
        self.lines.logret2[0] = self.logret2.rets[self.logret2.dtkey]
