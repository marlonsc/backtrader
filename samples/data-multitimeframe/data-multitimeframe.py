"""data-multitimeframe.py module.

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

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
from backtrader import (
    ReplayerDaily,
    ReplayerMonthly,
    ReplayerWeekly,
    ResamplerDaily,
    ResamplerMonthly,
    ResamplerWeekly,
)


class SMAStrategy(bt.Strategy):
""""""
""""""
""""""
""""""
""""""
""""""
""""""
    parser = argparse.ArgumentParser(description="Pandas test script")

    parser.add_argument(
        "--dataname", default="", required=False, help="File Data to Load"
    )

    parser.add_argument(
        "--dataname2",
        default="",
        required=False,
        help="Larger timeframe file to load",
    )

    parser.add_argument(
        "--runnext",
        action="store_true",
        help="Use next by next instead of runonce",
    )

    parser.add_argument(
        "--nopreload", action="store_true", help="Do not preload the data"
    )

    parser.add_argument(
        "--oldsync",
        action="store_true",
        help="Use old data synchronization method",
    )

    parser.add_argument("--oldrs", action="store_true", help="Use old resampler")

    parser.add_argument(
        "--replay", action="store_true", help="Replay instead of resample"
    )

    parser.add_argument(
        "--noresample",
        action="store_true",
        help="Do not resample, rather load larger timeframe",
    )

    parser.add_argument(
        "--timeframe",
        default="weekly",
        required=False,
        choices=["daily", "weekly", "monthly"],
        help="Timeframe to resample to",
    )

    parser.add_argument(
        "--compression",
        default=1,
        required=False,
        type=int,
        help="Compress n bars into 1",
    )

    parser.add_argument(
        "--indicators",
        action="store_true",
        help="Wether to apply Strategy with indicators",
    )

    parser.add_argument(
        "--onlydaily",
        action="store_true",
        help="Indicator only to be applied to daily timeframe",
    )

    parser.add_argument(
        "--period",
        default=10,
        required=False,
        type=int,
        help="Period to apply to indicator",
    )

    parser.add_argument(
        "--plot", required=False, action="store_true", help="Plot the chart"
    )

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
