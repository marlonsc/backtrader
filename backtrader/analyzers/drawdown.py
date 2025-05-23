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
from backtrader.utils import AutoOrderedDict

__all__ = ["DrawDown", "TimeDrawDown"]


class DrawDown(bt.Analyzer):
    """This analyzer calculates trading system drawdowns stats such as drawdown
    values in %s and in dollars, max drawdown in %s and in dollars, drawdown
    length and drawdown max length


    :returns: drawdown stats as values, the following keys/attributes are available:

        - ``drawdown`` - drawdown value in 0.xx %
        - ``moneydown`` - drawdown value in monetary units
        - ``len`` - drawdown length

        - ``max.drawdown`` - max drawdown value in 0.xx %
        - ``max.moneydown`` - max drawdown value in monetary units
        - ``max.len`` - max drawdown length

    """

    params = (("fund", None),)

    def start(self):
        """ """
        super(DrawDown, self).start()
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund

    def create_analysis(self):
        """ """
        self.rets = AutoOrderedDict()  # dict with . notation

        self.rets.len = 0
        self.rets.drawdown = 0.0
        self.rets.moneydown = 0.0

        self.rets.max.len = 0.0
        self.rets.max.drawdown = 0.0
        self.rets.max.moneydown = 0.0

        self._maxvalue = float("-inf")  # any value will outdo it

    def stop(self):
        """ """
        self.rets._close()  # . notation cannot create more keys

    def notify_fund(self, cash, value, fundvalue, shares):
        """

        :param cash:
        :param value:
        :param fundvalue:
        :param shares:

        """
        if not self._fundmode:
            self._value = value  # record current value
            self._maxvalue = max(self._maxvalue, value)  # update peak value
        else:
            self._value = fundvalue  # record current value
            self._maxvalue = max(self._maxvalue, fundvalue)  # update peak

    def next(self):
        """ """
        r = self.rets

        # calculate current drawdown values
        r.moneydown = moneydown = round(self._maxvalue - self._value, 2)
        r.drawdown = drawdown = round(100.0 * moneydown / self._maxvalue, 2)

        # maxximum drawdown values
        r.max.moneydown = max(r.max.moneydown, moneydown)
        r.max.drawdown = maxdrawdown = max(r.max.drawdown, drawdown)

        r.len = r.len + 1 if drawdown else 0
        r.max.len = max(r.max.len, r.len)


class TimeDrawDown(bt.TimeFrameAnalyzerBase):
    """This analyzer calculates trading system drawdowns on the chosen
    timeframe which can be different from the one used in the underlying data


    :returns: drawdown stats as values, the following keys/attributes are available:

        - ``drawdown`` - drawdown value in 0.xx %
        - ``maxdrawdown`` - drawdown value in monetary units
        - ``maxdrawdownperiod`` - drawdown length

      - Those are available during runs as attributes
        - ``dd``
        - ``maxdd``
        - ``maxddlen``

    """

    params = (("fund", None),)

    def start(self):
        """ """
        super(TimeDrawDown, self).start()
        if self.p.fund is None:
            self._fundmode = self.strategy.broker.fundmode
        else:
            self._fundmode = self.p.fund
        self.dd = 0.0
        self.maxdd = 0.0
        self.maxddlen = 0
        self.peak = float("-inf")
        self.ddlen = 0

    def on_dt_over(self):
        """ """
        if not self._fundmode:
            value = self.strategy.broker.getvalue()
        else:
            value = self.strategy.broker.fundvalue

        # update the maximum seen peak
        if value > self.peak:
            self.peak = value
            self.ddlen = 0  # start of streak

        # calculate the current drawdown
        self.dd = dd = 100.0 * (self.peak - value) / self.peak
        self.ddlen += bool(dd)  # if peak == value -> dd = 0

        # update the maxdrawdown if needed
        self.maxdd = max(self.maxdd, dd)
        self.maxddlen = max(self.maxddlen, self.ddlen)

    def stop(self):
        """ """
        self.rets["maxdrawdown"] = round(self.maxdd, 2)
        self.rets["maxdrawdownperiod"] = self.maxddlen
