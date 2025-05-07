"""tcal-intra.py module.

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


class NYSE_2016(bt.TradingCalendar):
""""""
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
        description="Trading Calendar Sample",
    )

    parser.add_argument(
        "--data0",
        default="yhoo-2016-11.csv",
        required=False,
        help="Data to read in",
    )

    # Defaults for dates
    parser.add_argument(
        "--fromdate",
        required=False,
        default="2016-01-01",
        help="Date[time] in YYYY-MM-DD[THH:MM:SS] format",
    )

    parser.add_argument(
        "--todate",
        required=False,
        default="2016-12-31",
        help="Date[time] in YYYY-MM-DD[THH:MM:SS] format",
    )

    parser.add_argument(
        "--cerebro",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--broker",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--sizer",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--strat",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--plot",
        required=False,
        default="",
        nargs="?",
        const="{}",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    pgroup = parser.add_mutually_exclusive_group(required=False)
    pgroup.add_argument(
        "--pandascal",
        required=False,
        action="store",
        default="",
        help="Name of trading calendar to use",
    )

    pgroup.add_argument(
        "--owncal",
        required=False,
        action="store_true",
        help="Apply custom NYSE 2016 calendar",
    )

    parser.add_argument(
        "--timeframe",
        required=False,
        action="store",
        default="Days",
        choices=["Days"],
        help="Timeframe to resample to",
    )

    return parser.parse_args(pargs)


if __name__ == "__main__":
    runstrat()
