"""sigsmacross.py module.

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


class SmaCross(bt.SignalStrategy):
""""""
"""Args::
    order:"""
"""Args::
    trade:"""
""""""
"""Args::
    pargs: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="sigsmacross",
    )

    parser.add_argument("--data", required=False, default="YHOO", help="Yahoo Ticker")

    parser.add_argument(
        "--fromdate",
        required=False,
        default="2011-01-01",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        required=False,
        default="2012-12-31",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--cash",
        required=False,
        action="store",
        type=float,
        default=10000,
        help="Starting cash",
    )

    parser.add_argument(
        "--stake",
        required=False,
        action="store",
        type=int,
        default=1,
        help="Stake to apply",
    )

    parser.add_argument(
        "--strat",
        required=False,
        action="store",
        default="",
        help="Arguments for the strategy",
    )

    parser.add_argument(
        "--plot",
        "-p",
        nargs="?",
        required=False,
        metavar="kwargs",
        const="{}",
        help=(
            "Plot the read data applying any kwargs passed\n"
            "\n"
            "For example:\n"
            "\n"
            '  --plot style="candle" (to plot candles)\n'
        ),
    )

    return parser.parse_args(pargs)


if __name__ == "__main__":
    runstrat()
