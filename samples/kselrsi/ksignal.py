"""ksignal.py module.

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


class TheStrategy(bt.SignalStrategy):
""""""
"""Args::
    order:"""
""""""
"""Args::
    pargs: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample after post at keithselover.wordpress.com",
    )

    parser.add_argument("--data", required=False, default="XOM", help="Yahoo Ticker")

    parser.add_argument(
        "--fromdate",
        required=False,
        default="2012-09-01",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        required=False,
        default="2016-01-01",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--cash",
        required=False,
        action="store",
        type=float,
        default=100000,
        help="Cash to start with",
    )

    parser.add_argument(
        "--stake",
        required=False,
        action="store",
        type=int,
        default=100,
        help="Cash to start with",
    )

    parser.add_argument(
        "--coc",
        required=False,
        action="store_true",
        help="Buy on close of same bar as order is issued",
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
