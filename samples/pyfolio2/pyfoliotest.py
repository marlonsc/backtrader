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
import collections
import datetime

import backtrader as bt


class St(bt.SignalStrategy):
""""""
""""""
""""""
""""""
"""Args::
    args: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for pivot point and cross plotting",
    )

    parser.add_argument("--data0", required=True, help="Data to be read in")

    parser.add_argument(
        "--timeframe",
        required=False,
        default=_TFS[0],
        choices=_TFS,
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--compression",
        required=False,
        default=1,
        type=int,
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--fromdate",
        required=False,
        default="2013-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        required=False,
        default="2015-12-31",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--stake",
        required=False,
        action="store",
        default=10,
        type=int,
        help="Stake size",
    )

    parser.add_argument(
        "--short", required=False, action="store_true", help="Go short too"
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
        "--pyfolio",
        required=False,
        action="store_true",
        help="Do pyfolio things",
    )

    parser.add_argument(
        "--pftimeframe",
        required=False,
        default="days",
        choices=_TFS,
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--printout", required=False, action="store_true", help="Print infos"
    )

    parser.add_argument(
        "--printdata",
        required=False,
        action="store_true",
        help="Print data lines",
    )

    # Plot options
    parser.add_argument(
        "--plot",
        "-p",
        nargs="?",
        required=False,
        metavar="kwargs",
        const=True,
        help=(
            "Plot the read data applying any kwargs passed\n"
            "\n"
            "For example:\n"
            "\n"
            '  --plot style="candle" (to plot candles)\n'
        ),
    )

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
