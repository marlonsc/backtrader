"""order-execution.py module.

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

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class OrderExecutionStrategy(bt.Strategy):
""""""
"""Logging function fot this strategy

Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        dt = dt or self.data.datetime[0]
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        print("%s, %s" % (dt.isoformat(), txt))

    def notify_order(self, order):
"""Args::
    order:"""
""""""
""""""
""""""
"""Args::
    args:"""
""""""
    parser = argparse.ArgumentParser(description="Showcase for Order Execution Types")

    parser.add_argument(
        "--infile",
        "-i",
        required=False,
        default="../../datas/2006-day-001.txt",
        help="File to be read in",
    )

    parser.add_argument(
        "--csvformat",
        "-c",
        required=False,
        default="bt",
        choices=[
            "bt",
            "visualchart",
            "sierrachart",
            "yahoo",
            "yahoo_unreversed",
        ],
        help="CSV Format",
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        required=False,
        default=None,
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        required=False,
        default=None,
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--plot",
        "-p",
        action="store_true",
        required=False,
        help="Plot the read data",
    )

    parser.add_argument(
        "--plotstyle",
        "-ps",
        required=False,
        default="bar",
        choices=["bar", "line", "candle"],
        help="Plot the read data",
    )

    parser.add_argument(
        "--numfigs",
        "-n",
        required=False,
        default=1,
        help="Plot using n figures",
    )

    parser.add_argument(
        "--smaperiod",
        "-s",
        required=False,
        default=15,
        help="Simple Moving Average Period",
    )

    parser.add_argument(
        "--exectype",
        "-e",
        required=False,
        default="Market",
        help="Execution Type: Market (default), Close, Limit, Stop, StopLimit",
    )

    parser.add_argument(
        "--valid",
        "-v",
        required=False,
        default=0,
        type=int,
        help="Validity for Limit sample: default 0 days",
    )

    parser.add_argument(
        "--perc1",
        "-p1",
        required=False,
        default=0.0,
        type=float,
        help=(
            "%% distance from close price at order creation"
            " time for the limit/trigger price in Limit/Stop"
            " orders"
        ),
    )

    parser.add_argument(
        "--perc2",
        "-p2",
        required=False,
        default=0.0,
        type=float,
        help=(
            "%% distance from close price at order creation"
            " time for the limit price in StopLimit orders"
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
