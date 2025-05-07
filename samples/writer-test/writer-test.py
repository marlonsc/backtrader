"""writer-test.py module.

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
from backtrader.analyzers import SQN


class LongShortStrategy(bt.Strategy):
    """This strategy buys/sells upong the close price crossing
upwards/downwards a Simple Moving Average.
It can be a long-only strategy by setting the param "onlylong" to True"""

    params = dict(
        period=15,
        stake=1,
        printout=False,
        onlylong=False,
        csvcross=False,
    )

    def start(self):
""""""
""""""
"""Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        if self.p.printout:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
""""""
""""""
"""Args::
    order:"""
"""Args::
    trade:"""
""""""
""""""
    parser = argparse.ArgumentParser(description="MultiData Strategy")

    parser.add_argument(
        "--data",
        "-d",
        default="../../datas/2006-day-001.txt",
        help="data to add to the system",
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        default="2006-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        default="2006-12-31",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--period",
        default=15,
        type=int,
        help="Period to apply to the Simple Moving Average",
    )

    parser.add_argument(
        "--onlylong", "-ol", action="store_true", help="Do only long operations"
    )

    parser.add_argument(
        "--writercsv",
        "-wcsv",
        action="store_true",
        help="Tell the writer to produce a csv stream",
    )

    parser.add_argument(
        "--csvcross",
        action="store_true",
        help="Output the CrossOver signals to CSV",
    )

    parser.add_argument("--cash", default=100000, type=int, help="Starting Cash")

    parser.add_argument(
        "--comm", default=2, type=float, help="Commission for operation"
    )

    parser.add_argument("--mult", default=10, type=int, help="Multiplier for futures")

    parser.add_argument(
        "--margin", default=2000.0, type=float, help="Margin for each future"
    )

    parser.add_argument(
        "--stake", default=1, type=int, help="Stake to apply in each operation"
    )

    parser.add_argument("--plot", "-p", action="store_true", help="Plot the read data")

    parser.add_argument("--numfigs", "-n", default=1, help="Plot using numfigs figures")

    return parser.parse_args()


if __name__ == "__main__":
    runstrategy()
