"""vwr.py module.

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

TFRAMES = dict(
    days=bt.TimeFrame.Days,
    weeks=bt.TimeFrame.Weeks,
    months=bt.TimeFrame.Months,
    years=bt.TimeFrame.Years,
)


def runstrat(pargs=None):
"""Args::
    pargs: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="VWR",
    )

    parser.add_argument(
        "--data",
        "-d",
        default="../../datas/2005-2006-day-001.txt",
        help="data to add to the system",
    )

    parser.add_argument(
        "--cash", default=None, type=float, required=False, help="Starting Cash"
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        default=None,
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        default=None,
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--writercsv",
        "-wcsv",
        action="store_true",
        help="Tell the writer to produce a csv stream",
    )

    parser.add_argument(
        "--tframe",
        "--timeframe",
        default=None,
        required=False,
        choices=TFRAMES.keys(),
        help="TimeFrame for the Returns/Sharpe calculations",
    )

    parser.add_argument(
        "--sigma-max",
        required=False,
        action="store",
        type=float,
        default=None,
        help="VWR Sigma Max",
    )

    parser.add_argument(
        "--tau",
        required=False,
        action="store",
        type=float,
        default=None,
        help="VWR tau factor",
    )

    parser.add_argument(
        "--tann",
        required=False,
        action="store",
        type=float,
        default=None,
        help="Annualization factor",
    )

    parser.add_argument(
        "--stddev-sample",
        required=False,
        action="store_true",
        help="Consider Bessels correction for stddeviation",
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
