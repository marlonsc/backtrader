"""order_target.py module.

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
from datetime import datetime

import backtrader as bt


class TheStrategy(bt.Strategy):
    """This strategy is loosely based on some of the examples from the Van
K. Tharp book: *Trade Your Way To Financial Freedom*. The logic:
- Enter the market if:
- The MACD.macd line crosses the MACD.signal line to the upside
- The Simple Moving Average has a negative direction in the last x
periods (actual value below value x periods ago)
- Set a stop price x times the ATR value away from the close
- If in the market:
- Check if the current close has gone below the stop price. If yes,
exit.
- If not, update the stop price if the new stop price would be higher
than the current"""

    params = (
        ("use_target_size", False),
        ("use_target_value", False),
        ("use_target_percent", False),
    )

    def notify_order(self, order):
"""Args::
    order:"""
""""""
""""""
"""Args::
    args: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for Order Target",
    )

    parser.add_argument(
        "--data",
        required=False,
        default="../../datas/yhoo-1996-2015.txt",
        help="Specific data to be read in",
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
        "--cash",
        required=False,
        action="store",
        type=float,
        default=1000000,
        help="Ending date in YYYY-MM-DD format",
    )

    pgroup = parser.add_mutually_exclusive_group(required=True)

    pgroup.add_argument(
        "--target-size",
        required=False,
        action="store_true",
        help="Use order_target_size",
    )

    pgroup.add_argument(
        "--target-value",
        required=False,
        action="store_true",
        help="Use order_target_value",
    )

    pgroup.add_argument(
        "--target-percent",
        required=False,
        action="store_true",
        help="Use order_target_percent",
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
