"""sizertest.py module.

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


class CloseSMA(bt.Strategy):
""""""
""""""
""""""
""""""
"""Args::
    comminfo: 
    cash: 
    data: 
    isbuy:"""
    isbuy:"""
        if isbuy:
            return self.p.stake

        # Sell situation
        position = self.broker.getposition(data)
        if not position.size:
            return 0  # do not sell if nothing is open

        return self.p.stake


class FixedReverser(bt.Sizer):
""""""
"""Args::
    comminfo: 
    cash: 
    data: 
    isbuy:"""
    isbuy:"""
        position = self.strategy.getposition(data)
        size = self.p.stake * (1 + (position.size != 0))
        return size


def runstrat(args=None):
"""Args::
    args: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for sizer",
    )

    parser.add_argument(
        "--data0",
        required=False,
        default="../../datas/yhoo-1996-2015.txt",
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
        "--cash",
        required=False,
        action="store",
        type=float,
        default=50000,
        help="Cash to start with",
    )

    parser.add_argument(
        "--longonly",
        required=False,
        action="store_true",
        help="Use the LongOnly sizer",
    )

    parser.add_argument(
        "--stake",
        required=False,
        action="store",
        type=int,
        default=1,
        help="Stake to pass to the sizers",
    )

    parser.add_argument(
        "--period",
        required=False,
        action="store",
        type=int,
        default=15,
        help="Period for the Simple Moving Average",
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
