"""calendar-days.py module.

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
import backtrader.filters as btfilters
import backtrader.indicators as btind


def runstrat():
""""""
""""""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Calendar Days Filter Sample",
    )

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
        "--calendar",
        "-cal",
        required=False,
        action="store_true",
        help="Add a CalendarDays filter",
    )

    parser.add_argument(
        "--fprice",
        required=False,
        default=None,
        help="Use as fill for price (None for previous close)",
    )

    parser.add_argument(
        "--fvol",
        required=False,
        default=0.0,
        type=float,
        help="Use as fill volume for missing bar (def: 0.0)",
    )

    parser.add_argument(
        "--sma",
        required=False,
        action="store_true",
        help="Add a Simple Moving Average",
    )

    parser.add_argument(
        "--period",
        default=15,
        type=int,
        help="Period to apply to the Simple Moving Average",
    )

    parser.add_argument(
        "--writer", "-w", action="store_true", help="Add a writer to cerebro"
    )

    parser.add_argument(
        "--wrcsv",
        "-wc",
        action="store_true",
        help="Enable CSV Output in the writer",
    )

    parser.add_argument("--plot", "-p", action="store_true", help="Plot the read data")

    parser.add_argument("--numfigs", "-n", default=1, help="Plot using numfigs figures")

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
