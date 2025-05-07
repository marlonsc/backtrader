"""weekdaysaligner.py module.

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
import backtrader.utils.flushfile

# from wkdaysfiller import WeekDaysFiller
from weekdaysfiller import WeekDaysFiller


class St(bt.Strategy):
""""""
""""""
""""""
""""""
""""""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for aligning with trade ",
    )

    parser.add_argument(
        "--online",
        required=False,
        action="store_true",
        help="Fetch data online from Yahoo",
    )

    parser.add_argument("--data0", required=True, help="Data 0 to be read in")
    parser.add_argument("--data1", required=False, help="Data 1 to be read in")

    parser.add_argument(
        "--sma",
        required=False,
        default=0,
        type=int,
        help="Add a sma to the datas",
    )

    parser.add_argument(
        "--fillclose",
        required=False,
        action="store_true",
        help="Fill with Close price instead of NaN",
    )

    parser.add_argument(
        "--filler",
        required=False,
        action="store_true",
        help="Add Filler to Datas 0 and 1",
    )

    parser.add_argument(
        "--filler0",
        required=False,
        action="store_true",
        help="Add Filler to Data 0",
    )

    parser.add_argument(
        "--filler1",
        required=False,
        action="store_true",
        help="Add Filler to Data 1",
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        default="2012-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        default="2012-12-31",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument("--plot", required=False, action="store_true", help="Do plot")

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
