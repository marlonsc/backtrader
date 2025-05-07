"""signals-strategy.py module.

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

MAINSIGNALS = collections.OrderedDict(
    (
        ("longshort", bt.SIGNAL_LONGSHORT),
        ("longonly", bt.SIGNAL_LONG),
        ("shortonly", bt.SIGNAL_SHORT),
    )
)

EXITSIGNALS = {
    "longexit": bt.SIGNAL_LONGEXIT,
    "shortexit": bt.SIGNAL_LONGEXIT,
}


class SMACloseSignal(bt.Indicator):
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
        description="Sample for Signal concepts",
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
        "--smaperiod",
        required=False,
        action="store",
        type=int,
        default=30,
        help="Period for the moving average",
    )

    parser.add_argument(
        "--exitperiod",
        required=False,
        action="store",
        type=int,
        default=5,
        help="Period for the exit control SMA",
    )

    parser.add_argument(
        "--signal",
        required=False,
        action="store",
        default=MAINSIGNALS.keys()[0],
        choices=MAINSIGNALS,
        help="Signal type to use for the main signal",
    )

    parser.add_argument(
        "--exitsignal",
        required=False,
        action="store",
        default=None,
        choices=EXITSIGNALS,
        help="Signal type to use for the exit signal",
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
