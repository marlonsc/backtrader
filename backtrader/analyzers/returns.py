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

import math

import backtrader as bt
from backtrader import TimeFrameAnalyzerBase


class Returns(TimeFrameAnalyzerBase):
    """Total, Average, Compound and Annualized Returns calculated using a
    logarithmic approach
    
    See:
    
      - https://www.crystalbull.com/sharpe-ratio-better-with-log-returns/


    :returns: each return as keys
    
        The returned dict the following keys:
    
          - ``rtot``: Total compound return
          - ``ravg``: Average return for the entire period (timeframe specific)
          - ``rnorm``: Annualized/Normalized return
          - ``rnorm100``: Annualized/Normalized return expressed in 100%

    """

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
        """ """
        super(Returns, self).start()
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

        if not self._fundmode:
            self._value_start = self.strategy.broker.getvalue()
        else:
            self._value_start = self.strategy.broker.fundvalue

        self._tcount = 0

    def stop(self):
        """ """
        super(Returns, self).stop()

        if not self._fundmode:
            self._value_end = self.strategy.broker.getvalue()
        else:
            self._value_end = self.strategy.broker.fundvalue

        # Compound return
        try:
            nlrtot = self._value_end / self._value_start
        except ZeroDivisionError:
            rtot = float("-inf")
        else:
            if nlrtot < 0.0:
                rtot = float("-inf")
            else:
                rtot = math.log(nlrtot)

        self.rets["rtot"] = round(rtot, 6)

        # Average return
        try:
            ravg = rtot / self._tcount
        except ZeroDivisionError:
            ravg = float("-inf")
        self.rets["ravg"] = round(ravg, 6)

        # Annualized normalized return
        tann = self.p.tann or self._TANN.get(self.timeframe, None)
        if tann is None:
            tann = self._TANN.get(self.data._timeframe, 1.0)  # assign default

        if ravg > float("-inf"):
            self.rets["rnorm"] = rnorm = round(math.expm1(ravg * tann), 6)
        else:
            self.rets["rnorm"] = rnorm = round(ravg, 6)

        self.rets["rnorm100"] = round(rnorm * 100.0, 4)  # human readable %

    def _on_dt_over(self):
        """ """
        self._tcount += 1  # count the subperiod
