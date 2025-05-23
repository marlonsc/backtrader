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

from ..observer import Observer


class BuySell(Observer):
    """This observer keeps track of the individual buy/sell orders (individual
    executions) and will plot them on the chart along the data around the
    execution price level


    """

    lines = (
        "buy",
        "sell",
    )

    plotinfo = dict(plot=True, subplot=False, plotlinelabels=True)
    plotlines = dict(
        buy=dict(marker="^", markersize=8.0, color="lime", fillstyle="full", ls=""),
        sell=dict(marker="v", markersize=8.0, color="red", fillstyle="full", ls=""),
    )

    params = (
        ("barplot", False),  # plot above/below max/min for clarity in bar plot
        ("bardist", 0.015),  # distance to max/min in absolute perc
    )

    @staticmethod
    def _get_bar_dist(data, bardist):
        """

        :param data:
        :param bardist:

        """
        return abs(data.low[0] - data.high[0]) * (1 + bardist)

    def next(self):
        """ """
        buy = list()
        sell = list()

        for order in self._owner._orderspending:
            if order.data is not self.data or not order.executed.size:
                continue

            if order.isbuy():
                buy.append(order.executed.price)
            else:
                sell.append(order.executed.price)

        # Take into account replay ... something could already be in there
        # Write down the average buy/sell price

        # BUY
        curbuy = self.lines.buy[0]
        if curbuy != curbuy:  # NaN
            curbuy = 0.0
            self.curbuylen = curbuylen = 0
        else:
            curbuylen = self.curbuylen

        buyops = curbuy + math.fsum(buy)
        buylen = curbuylen + len(buy)

        value = buyops / float(buylen or "NaN")
        if not self.p.barplot:
            self.lines.buy[0] = value
        elif value == value:  # Not NaN
            pbuy = self.data.low[0] - self._get_bar_dist(self.data, self.p.bardist)
            self.lines.buy[0] = pbuy

        # Update buylen values
        curbuy = buyops
        self.curbuylen = buylen

        # SELL
        cursell = self.lines.sell[0]
        if cursell != cursell:  # NaN
            cursell = 0.0
            self.curselllen = curselllen = 0
        else:
            curselllen = self.curselllen

        sellops = cursell + math.fsum(sell)
        selllen = curselllen + len(sell)

        value = sellops / float(selllen or "NaN")
        if not self.p.barplot:
            self.lines.sell[0] = value
        elif value == value:  # Not NaN
            psell = self.data.high[0] + self._get_bar_dist(self.data, self.p.bardist)
            self.lines.sell[0] = psell

        # Update selllen values
        cursell = sellops
        self.curselllen = selllen
