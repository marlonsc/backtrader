"""plot-same-axis.py module.

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

# The above could be sent to an independent module
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class PlotStrategy(bt.Strategy):
    """The strategy does nothing but create indicators for plotting purposes"""

    params = dict(
        smasubplot=False,  # default for Moving averages
        nomacdplot=False,
        rsioverstoc=False,
        rsioversma=False,
        stocrsi=False,
        stocrsilabels=False,
    )

    def __init__(self):
""""""
""""""
""""""
    parser = argparse.ArgumentParser(description="Plotting Example")

    parser.add_argument(
        "--data",
        "-d",
        default="../../datas/2006-day-001.txt",
        help="data to add to the system",
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        default="2006-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        default="2006-12-31",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--stdstats", "-st", action="store_true", help="Show standard observers"
    )

    parser.add_argument(
        "--smasubplot",
        "-ss",
        action="store_true",
        help="Put SMA on own subplot/axis",
    )

    parser.add_argument(
        "--nomacdplot",
        "-nm",
        action="store_true",
        help="Hide the indicator from the plot",
    )

    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument(
        "--rsioverstoc",
        "-ros",
        action="store_true",
        help="Plot the RSI indicator on the Stochastic axis",
    )

    group.add_argument(
        "--rsioversma",
        "-rom",
        action="store_true",
        help="Plot the RSI indicator on the SMA axis",
    )

    group.add_argument(
        "--stocrsi",
        "-strsi",
        action="store_true",
        help="Plot the Stochastic indicator on the RSI axis",
    )

    parser.add_argument(
        "--stocrsilabels",
        action="store_true",
        help="Plot line names instead of indicator name",
    )

    parser.add_argument("--numfigs", "-n", default=1, help="Plot using numfigs figures")

    return parser.parse_args()


if __name__ == "__main__":
    runstrategy()
