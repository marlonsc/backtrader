"""multi-copy.py module.

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


class TheStrategy(bt.Strategy):
    """This strategy is capable of:
- Going Long with a Moving Average upwards CrossOver
- Going Long again with a MACD upwards CrossOver
- Closing the aforementioned longs with the corresponding downwards
crossovers"""

    params = (
        ("myname", None),
        ("dtarget", None),
        ("stake", 100),
        ("macd1", 12),
        ("macd2", 26),
        ("macdsig", 9),
        ("sma1", 10),
        ("sma2", 30),
    )

    def notify_order(self, order):
"""Args::
    order:"""
""""""
""""""
""""""
    """Subclass of TheStrategy to simply change the parameters"""

    params = (
        ("stake", 200),
        ("macd1", 15),
        ("macd2", 22),
        ("macdsig", 7),
        ("sma1", 15),
        ("sma2", 50),
    )


def runstrat(args=None):
"""Args::
    args: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for Tharp example with MACD",
    )

    # pgroup = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument(
        "--data0",
        required=False,
        default="../../datas/yhoo-1996-2014.txt",
        help="Specific data0 to be read in",
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
        default=50000,
        help="Cash to start with",
    )

    parser.add_argument(
        "--copydata",
        required=False,
        action="store_true",
        help="Copy Data for 2nd strategy",
    )

    parser.add_argument(
        "--st0",
        required=False,
        action="store",
        default=None,
        help=(
            "Params for 1st strategy: as a list of comma "
            "separated name=value pairs like: "
            "stake=100,macd1=12,macd2=26,macdsig=9,"
            "sma1=10,sma2=30"
        ),
    )

    parser.add_argument(
        "--st1",
        required=False,
        action="store",
        default=None,
        help=(
            "Params for 1st strategy: as a list of comma "
            "separated name=value pairs like: "
            "stake=200,macd1=15,macd2=22,macdsig=7,"
            "sma1=15,sma2=50"
        ),
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
