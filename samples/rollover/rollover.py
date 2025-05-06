"""rollover.py module.

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
import calendar
import datetime

import backtrader as bt


class TheStrategy(bt.Strategy):
""""""
""""""
""""""
"""Args::
    dt: 
    d:"""
    d:"""
    # Check if the date is in the week where the 3rd friday of Mar/Jun/Sep/Dec

    # EuroStoxx50 expiry codes: MY
    # M -> H, M, U, Z (Mar, Jun, Sep, Dec)
    # Y -> 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 -> year code. 5 -> 2015
    MONTHS = dict(H=3, M=6, U=9, Z=12)

    M = MONTHS[d._dataname[-2]]

    centuria, year = divmod(dt.year, 10)
    decade = centuria * 10

    YCode = int(d._dataname[-1])
    Y = decade + YCode
    if Y < dt.year:  # Example: year 2019 ... YCode is 0 for 2023
        Y += 10

    exp_day = 21 - (calendar.weekday(Y, M, 1) + 2) % 7
    exp_dt = datetime.datetime(Y, M, exp_day)

    # Get the year, week numbers
    exp_year, exp_week, _ = exp_dt.isocalendar()
    dt_year, dt_week, _ = dt.isocalendar()

    # print('dt {} vs {} exp_dt'.format(dt, exp_dt))
    # print('dt_week {} vs {} exp_week'.format(dt_week, exp_week))

    # can switch if in same week
    return (dt_year, dt_week) == (exp_year, exp_week)


def checkvolume(d0, d1):
"""Args::
    d0: 
    d1:"""
    d1:"""
    return d0.volume[0] < d1.volume[0]  # Switch if volume from d0 < d1


def runstrat(args=None):
"""Args::
    args: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for Roll Over of Futures",
    )

    parser.add_argument(
        "--no-cerebro",
        required=False,
        action="store_true",
        help="Use RollOver Directly",
    )

    parser.add_argument("--rollover", required=False, action="store_true")

    parser.add_argument(
        "--checkdate",
        required=False,
        action="store_true",
        help="Change during expiration week",
    )

    parser.add_argument(
        "--checkcondition",
        required=False,
        action="store_true",
        help="Change when a given condition is met",
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
