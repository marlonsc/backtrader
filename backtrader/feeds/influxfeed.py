"""influxfeed.py module.

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

import datetime as dt

import backtrader as bt
import backtrader.feed as feed

from ..utils import date2num

TIMEFRAMES = dict(
    (
        (bt.TimeFrame.Seconds, "s"),
        (bt.TimeFrame.Minutes, "m"),
        (bt.TimeFrame.Days, "d"),
        (bt.TimeFrame.Weeks, "w"),
        (bt.TimeFrame.Months, "m"),
        (bt.TimeFrame.Years, "y"),
    )
)


class InfluxDB(feed.DataBase):
""""""
""""""
""""""
        try:
            bar = next(self.biter)
        except StopIteration:
            return False

        self.l.datetime[0] = date2num(
            dt.datetime.strptime(bar["time"], "%Y-%m-%dT%H:%M:%SZ")
        )

        self.l.open[0] = bar["open"]
        self.l.high[0] = bar["high"]
        self.l.low[0] = bar["low"]
        self.l.close[0] = bar["close"]
        self.l.volume[0] = bar["volume"]

        return True
