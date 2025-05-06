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

import collections
import math

import backtrader as bt

__all__ = ["LogReturnsRolling"]


class LogReturnsRolling(bt.TimeFrameAnalyzerBase):
    """This analyzer calculates rolling returns for a given timeframe and
compression

Returns:
    each return as keys"""

    params = (
        ("data", None),
        ("firstopen", True),
        ("fund", None),
    )

    def start(self):
        """ """
        super(LogReturnsRolling, self).start()
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

        self._values = collections.deque(
            [float("Nan")] * self.compression, maxlen=self.compression
        )

        if self.p.data is None:
            # keep the initial portfolio value if not tracing a data
            if not self._fundmode:
                self._lastvalue = self.strategy.broker.getvalue()
            else:
                self._lastvalue = self.strategy.broker.fundvalue

    def notify_fund(self, cash, value, fundvalue, shares):
        """Args:
    cash: 
    value: 
    fundvalue: 
    shares:"""
        if not self._fundmode:
            self._value = value if self.p.data is None else self.p.data[0]
        else:
            self._value = fundvalue if self.p.data is None else self.p.data[0]

    def _on_dt_over(self):
        """ """
        # next is called in a new timeframe period
        if self.p.data is None or len(self.p.data) > 1:
            # Not tracking a data feed or data feed has data already
            vst = self._lastvalue  # update value_start to last
        else:
            # The 1st tick has no previous reference, use the opening price
            vst = self.p.data.open[0] if self.p.firstopen else self.p.data[0]

        self._values.append(vst)  # push values backwards (and out)

    def next(self):
        """ """
        # Calculate the return
        super(LogReturnsRolling, self).next()
        self.rets[self.dtkey] = round(math.log(self._value / self._values[0]), 6)
        self._lastvalue = self._value  # keep last value
