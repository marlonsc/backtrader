"""multidata-strategy-unaligned.py module.

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

import argparse
import datetime

# The above could be sent to an independent module
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class MultiDataStrategy(bt.Strategy):
    """This strategy operates on 2 datas. The expectation is that the 2 datas are
correlated and the 2nd data is used to generate signals on the 1st
- Buy/Sell Operationss will be executed on the 1st data
- The signals are generated using a Simple Moving Average on the 2nd data
when the close price crosses upwwards/downwards
The strategy is a long-only strategy"""

    params = dict(
        period=15,
        stake=10,
        printout=True,
    )

    def log(self, txt, dt=None):
"""Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        if self.p.printout:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print("%s, %s" % (dt.isoformat(), txt))

    def notify_order(self, order):
"""Args::
    order:"""
""""""
""""""
""""""
""""""
""""""
    parser = argparse.ArgumentParser(description="MultiData Strategy")

    parser.add_argument(
        "--data0",
        "-d0",
        default="../../datas/orcl-2003-2005.txt",
        help="1st data into the system",
    )

    parser.add_argument(
        "--data1",
        "-d1",
        default="../../datas/yhoo-2003-2005.txt",
        help="2nd data into the system",
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        default="2003-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        default="2005-12-31",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--period",
        default=15,
        type=int,
        help="Period to apply to the Simple Moving Average",
    )

    parser.add_argument("--cash", default=100000, type=int, help="Starting Cash")

    parser.add_argument(
        "--runnext",
        action="store_true",
        help="Use next by next instead of runonce",
    )

    parser.add_argument(
        "--nopreload", action="store_true", help="Do not preload the data"
    )

    parser.add_argument(
        "--oldsync",
        action="store_true",
        help="Use old data synchronization method",
    )

    parser.add_argument(
        "--commperc",
        default=0.005,
        type=float,
        help="Percentage commission (0.005 is 0.5%%",
    )

    parser.add_argument(
        "--stake", default=10, type=int, help="Stake to apply in each operation"
    )

    parser.add_argument("--plot", "-p", action="store_true", help="Plot the read data")

    parser.add_argument("--numfigs", "-n", default=1, help="Plot using numfigs figures")

    return parser.parse_args()


if __name__ == "__main__":
    runstrategy()
