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

from backtrader import TimeFrameAnalyzerBase


class TimeReturn(TimeFrameAnalyzerBase):
    """This analyzer calculates the Returns by looking at the beginning
    and end of the timeframe


    :returns: each return as keys

    """

    params = (
        ("data", None),
        ("firstopen", True),
        ("fund", None),
    )

    def start(self):
        """ """
        super(TimeReturn, self).start()
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

        self._value_start = 0.0
        self._lastvalue = None
        if self.p.data is None:
            # keep the initial portfolio value if not tracing a data
            if not self._fundmode:
                self._lastvalue = self.strategy.broker.getvalue()
            else:
                self._lastvalue = self.strategy.broker.fundvalue

    def notify_fund(self, cash, value, fundvalue, shares):
        """

        :param cash:
        :param value:
        :param fundvalue:
        :param shares:

        """
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
        """ """
        # next is called in a new timeframe period
        # if self.p.data is None or len(self.p.data) > 1:
        if self.p.data is None or self._lastvalue is not None:
            self._value_start = self._lastvalue  # update value_start to last

        else:
            # The 1st tick has no previous reference, use the opening price
            if self.p.firstopen:
                self._value_start = self.p.data.open[0]
            else:
                self._value_start = self.p.data[0]

    def next(self):
        """ """
        # Calculate the return
        super(TimeReturn, self).next()
        self.rets[self.dtkey] = round(((self._value / self._value_start) - 1.0), 6)
        self._lastvalue = self._value  # keep last value

    def optimize(self):
        """Optimizies the object if optreturn is in effect"""
        super().optimize()

        self.strategy = None
