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

import backtrader as bt

from .. import Observer, TimeFrame


class TimeReturn(Observer):
    """This observer stores the *returns* of the strategy."""

    _stclock = True

    lines = ("timereturn",)
    plotinfo = dict(plot=True, subplot=True)
    plotlines = dict(timereturn=dict(_name="Return"))

    params = (
        ("timeframe", None),
        ("compression", None),
        ("fund", None),
    )

    def _plotlabel(self):
        """ """
        return [
            # Use the final tf/comp values calculated by the return analyzer
            TimeFrame.getname(self.treturn.timeframe, self.treturn.compression),
            str(self.treturn.compression),
        ]

    def __init__(self):
        """ """
        self.treturn = self._owner._addanalyzer_slave(
            bt.analyzers.TimeReturn, **self.p._getkwargs()
        )

    def next(self):
        """ """
        self.lines.timereturn[0] = self.treturn.rets.get(
            self.treturn.dtkey, float("NaN")
        )
