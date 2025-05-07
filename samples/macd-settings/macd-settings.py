"""macd-settings.py module.

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

BTVERSION = tuple(int(x) for x in bt.__version__.split("."))


class FixedPerc(bt.Sizer):
    """This sizer simply returns a fixed size for any operation"""

    params = (("perc", 0.20),)  # perc of cash to use for operation

    def _getsizing(self, comminfo, cash, data, isbuy):
"""Args::
    comminfo: 
    cash: 
    data: 
    isbuy:"""
    isbuy:"""
        cashtouse = self.p.perc * cash
        if BTVERSION > (1, 7, 1, 93):
            size = comminfo.getsize(data.close[0], cashtouse)
        else:
            size = cashtouse // data.close[0]
        return size


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
        # Standard MACD Parameters
        ("macd1", 12),
        ("macd2", 26),
        ("macdsig", 9),
        ("atrperiod", 14),  # ATR Period (standard)
        ("atrdist", 3.0),  # ATR distance for stop price
        ("smaperiod", 30),  # SMA Period (pretty standard)
        ("dirperiod", 10),  # Lookback period to consider SMA trend direction
    )

    def notify_order(self, order):
"""Args::
    order:"""
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
        description="Sample for Tharp example with MACD",
    )

    group1 = parser.add_mutually_exclusive_group(required=True)
    group1.add_argument(
        "--data",
        required=False,
        default=None,
        help="Specific data to be read in",
    )

    group1.add_argument(
        "--dataset",
        required=False,
        action="store",
        default=None,
        choices=DATASETS.keys(),
        help="Choose one of the predefined data sets",
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
        "--cashalloc",
        required=False,
        action="store",
        type=float,
        default=0.20,
        help="Perc (abs) of cash to allocate for ops",
    )

    parser.add_argument(
        "--commperc",
        required=False,
        action="store",
        type=float,
        default=0.0033,
        help="Perc (abs) commision in each operation. 0.001 -> 0.1%%, 0.01 -> 1%%",
    )

    parser.add_argument(
        "--macd1",
        required=False,
        action="store",
        type=int,
        default=12,
        help="MACD Period 1 value",
    )

    parser.add_argument(
        "--macd2",
        required=False,
        action="store",
        type=int,
        default=26,
        help="MACD Period 2 value",
    )

    parser.add_argument(
        "--macdsig",
        required=False,
        action="store",
        type=int,
        default=9,
        help="MACD Signal Period value",
    )

    parser.add_argument(
        "--atrperiod",
        required=False,
        action="store",
        type=int,
        default=14,
        help="ATR Period To Consider",
    )

    parser.add_argument(
        "--atrdist",
        required=False,
        action="store",
        type=float,
        default=3.0,
        help="ATR Factor for stop price calculation",
    )

    parser.add_argument(
        "--smaperiod",
        required=False,
        action="store",
        type=int,
        default=30,
        help="Period for the moving average",
    )

    parser.add_argument(
        "--dirperiod",
        required=False,
        action="store",
        type=int,
        default=10,
        help="Period for SMA direction calculation",
    )

    parser.add_argument(
        "--riskfreerate",
        required=False,
        action="store",
        type=float,
        default=0.01,
        help="Risk free rate in Perc (abs) of the asset for the Sharpe Ratio",
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
