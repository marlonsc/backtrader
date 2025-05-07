"""bidask-to-ohlc.py module.

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
)

import argparse

import backtrader as bt
import backtrader.feeds as btfeeds

#                        unicode_literals)


class St(bt.Strategy):
""""""
""""""
""""""
""""""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="BidAsk to OHLC",
    )

    parser.add_argument(
        "--data",
        required=False,
        default="../../datas/bidask2.csv",
        help="Data file to be read in",
    )

    parser.add_argument(
        "--compression",
        required=False,
        default=2,
        type=int,
        help="How much to compress the bars",
    )

    parser.add_argument(
        "--plot", required=False, action="store_true", help="Plot the vars"
    )

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
