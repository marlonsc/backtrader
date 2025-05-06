"""credit-interest.py module.

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
import itertools

import backtrader as bt


class SMACrossOver(bt.Signal):
""""""
""""""
""""""
""""""
""""""
"""Args::
    order:"""
"""Args::
    trade:"""
"""Args::
    args: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for Slippage",
    )

    parser.add_argument(
        "--data",
        required=False,
        default="../../datas/2005-2006-day-001.txt",
        help="Specific data to be read in",
    )

    parser.add_argument(
        "--fromdate",
        required=False,
        default=None,
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        required=False,
        default=None,
        help="Ending date in YYYY-MM-DD format",
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
        "--period1",
        required=False,
        action="store",
        type=int,
        default=10,
        help="Fast moving average period",
    )

    parser.add_argument(
        "--period2",
        required=False,
        action="store",
        type=int,
        default=30,
        help="Slow moving average period",
    )

    parser.add_argument(
        "--interest",
        required=False,
        action="store",
        default=0.0,
        type=float,
        help="Activate credit interest rate",
    )

    parser.add_argument(
        "--no-int2pnl",
        required=False,
        action="store_false",
        help="Do not assign interest to pnl",
    )

    parser.add_argument(
        "--interest_long",
        required=False,
        action="store_true",
        help="Credit interest rate for long positions",
    )

    pgroup = parser.add_mutually_exclusive_group()
    pgroup.add_argument(
        "--long",
        required=False,
        action="store_true",
        help="Do a long only strategy",
    )

    pgroup.add_argument(
        "--short",
        required=False,
        action="store_true",
        help="Do a long only strategy",
    )

    parser.add_argument(
        "--no-exit",
        required=False,
        action="store_true",
        help="The 1st taken position will not be exited",
    )

    parser.add_argument(
        "--stocklike",
        required=False,
        action="store_true",
        help="Consider the asset to be stocklike",
    )

    parser.add_argument(
        "--margin",
        required=False,
        action="store",
        default=0.0,
        type=float,
        help="Margin for future like instruments",
    )

    parser.add_argument(
        "--mult",
        required=False,
        action="store",
        default=1.0,
        type=float,
        help="Multiplier for future like instruments",
    )

    parser.add_argument(
        "--stake",
        required=False,
        action="store",
        default=10,
        type=int,
        help="Stake to apply",
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
