"""commission-schemes.py module.

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
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class SMACrossOver(bt.Strategy):
""""""
"""Logging function fot this strategy

Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def notify_order(self, order):
"""Args::
    order:"""
"""Args::
    trade:"""
""""""
""""""
""""""
""""""
    parser = argparse.ArgumentParser(
        description="Commission schemes",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
        "--stake", default=1, type=int, help="Stake to apply in each operation"
    )

    parser.add_argument(
        "--period",
        default=30,
        type=int,
        help="Period to apply to the Simple Moving Average",
    )

    parser.add_argument("--cash", default=10000.0, type=float, help="Starting Cash")

    parser.add_argument(
        "--comm",
        default=2.0,
        type=float,
        help=(
            "Commission factor for operation, either a"
            "percentage or a per stake unit absolute value"
        ),
    )

    parser.add_argument(
        "--mult",
        default=10,
        type=int,
        help="Multiplier for operations calculation",
    )

    parser.add_argument(
        "--margin",
        default=2000.0,
        type=float,
        help="Margin for futures-like operations",
    )

    parser.add_argument(
        "--commtype",
        required=False,
        default="none",
        choices=["none", "perc", "fixed"],
        help="Commission - choose none for the old CommissionInfo behavior",
    )

    parser.add_argument(
        "--stocklike",
        required=False,
        action="store_true",
        help="If the operation is for stock-like assets orfuture-like assets",
    )

    parser.add_argument(
        "--percrel",
        required=False,
        action="store_true",
        help="If perc is expressed in relative xx% ratherthan absolute value 0.xx",
    )

    parser.add_argument("--plot", "-p", action="store_true", help="Plot the read data")

    parser.add_argument("--numfigs", "-n", default=1, help="Plot using numfigs figures")

    return parser.parse_args()


if __name__ == "__main__":
    runstrategy()
