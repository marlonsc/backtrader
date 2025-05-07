"""slippage.py module.

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


class SMACrossOver(bt.Indicator):
""""""
""""""
""""""
"""Args::
    order:"""
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
        "--longonly",
        required=False,
        action="store_true",
        help="Long only strategy",
    )

    pgroup = parser.add_mutually_exclusive_group(required=False)
    pgroup.add_argument(
        "--slip_perc",
        required=False,
        default=None,
        type=float,
        help="Set the value for commission percentage",
    )

    pgroup.add_argument(
        "--slip_fixed",
        required=False,
        default=None,
        type=float,
        help="Set the value for commission percentage",
    )

    parser.add_argument(
        "--no-slip_match",
        required=False,
        action="store_true",
        help="Match by capping slippage at bar ends",
    )

    parser.add_argument(
        "--slip_out",
        required=False,
        action="store_true",
        help="Disable capping and return non-real prices",
    )

    parser.add_argument(
        "--slip_open",
        required=False,
        action="store_true",
        help="Slip even if match price is next open",
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
