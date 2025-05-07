"""pyfoliotest.py module.

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
import random

import backtrader as bt


class St(bt.Strategy):
""""""
""""""
""""""
""""""
"""Args::
    args: (Default value = None)"""
"""Args::
    args: (Default value = None)"""
    args: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for pivot point and cross plotting",
    )

    parser.add_argument(
        "--data0",
        required=False,
        default="../../datas/yhoo-1996-2015.txt",
        help="Data to be read in",
    )

    parser.add_argument(
        "--data1",
        required=False,
        default="../../datas/orcl-1995-2014.txt",
        help="Data to be read in",
    )

    parser.add_argument(
        "--data2",
        required=False,
        default="../../datas/nvda-1999-2014.txt",
        help="Data to be read in",
    )

    parser.add_argument(
        "--fromdate",
        required=False,
        default="2005-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        required=False,
        default="2006-12-31",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--printout",
        required=False,
        action="store_true",
        help="Print data lines",
    )

    parser.add_argument(
        "--cash",
        required=False,
        action="store",
        type=float,
        default=50000,
        help="Cash to start with",
    )

    parser.add_argument(
        "--plot", required=False, action="store_true", help="Plot the result"
    )

    parser.add_argument(
        "--plot-style",
        required=False,
        action="store",
        default="bar",
        choices=["bar", "candle", "line"],
        help="Plot style",
    )

    parser.add_argument(
        "--no-pyfolio",
        required=False,
        action="store_true",
        help="Do not do pyfolio things",
    )

    import sys

    aargs = args if args is not None else sys.argv[1:]
    return parser.parse_args(aargs)


if __name__ == "__main__":
    runstrat()
