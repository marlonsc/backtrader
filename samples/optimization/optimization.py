"""optimization.py module.

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
import time

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
from backtrader.utils.py3 import range


class OptimizeStrategy(bt.Strategy):
""""""
""""""
""""""
""""""
    parser = argparse.ArgumentParser(
        description="Optimization",
        formatter_class=argparse.RawTextHelpFormatter,
    )

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
        "--maxcpus",
        "-m",
        type=int,
        required=False,
        default=0,
        help=(
            "Number of CPUs to use in the optimization"
            "\n"
            "  - 0 (default): use all available CPUs\n"
            "  - 1 -> n: use as many as specified\n"
        ),
    )

    parser.add_argument(
        "--no-runonce",
        action="store_true",
        required=False,
        help="Run in next mode",
    )

    parser.add_argument(
        "--exactbars",
        required=False,
        type=int,
        default=0,
        help=(
            "Use the specified exactbars still compatible with preload\n"
            "  0 No memory savings\n"
            "  -1 Moderate memory savings\n"
            "  -2 Less moderate memory savings\n"
        ),
    )

    parser.add_argument(
        "--no-optdatas",
        action="store_true",
        required=False,
        help="Do not optimize data preloading in optimization",
    )

    parser.add_argument(
        "--no-optreturn",
        action="store_true",
        required=False,
        help="Do not optimize the returned values to save time",
    )

    parser.add_argument(
        "--ma_low",
        type=int,
        default=10,
        required=False,
        help="SMA range low to optimize",
    )

    parser.add_argument(
        "--ma_high",
        type=int,
        default=30,
        required=False,
        help="SMA range high to optimize",
    )

    parser.add_argument(
        "--m1_low",
        type=int,
        default=12,
        required=False,
        help="MACD Fast MA range low to optimize",
    )

    parser.add_argument(
        "--m1_high",
        type=int,
        default=20,
        required=False,
        help="MACD Fast MA range high to optimize",
    )

    parser.add_argument(
        "--m2_low",
        type=int,
        default=26,
        required=False,
        help="MACD Slow MA range low to optimize",
    )

    parser.add_argument(
        "--m2_high",
        type=int,
        default=30,
        required=False,
        help="MACD Slow MA range high to optimize",
    )

    parser.add_argument(
        "--m3_low",
        type=int,
        default=9,
        required=False,
        help="MACD Signal range low to optimize",
    )

    parser.add_argument(
        "--m3_high",
        type=int,
        default=15,
        required=False,
        help="MACD Signal range high to optimize",
    )

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
