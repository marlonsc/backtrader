"""vctest.py module.

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


class BtTestStrategy(bt.Strategy):
""""""
""""""
"""Args::
    data: 
    status:"""
    status:"""
        print("*" * 5, "DATA NOTIF:", data._getstatusname(status), *args)
        if status == data.LIVE:
            self.counttostop = self.p.stopafter
            self.datastatus = 1

    def notify_store(self, msg, *args, **kwargs):
"""Args::
    msg:"""
"""Args::
    order:"""
"""Args::
    trade:"""
""""""
"""Args::
    frompre: (Default value = False)"""
""""""
""""""
""""""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Test Visual Chart 6 integration",
    )

    parser.add_argument(
        "--exactbars",
        default=1,
        type=int,
        required=False,
        action="store",
        help="exactbars level, use 0/-1/-2 to enable plotting",
    )

    parser.add_argument(
        "--plot", required=False, action="store_true", help="Plot if possible"
    )

    parser.add_argument(
        "--stopafter",
        default=0,
        type=int,
        required=False,
        action="store",
        help="Stop after x lines of LIVE data",
    )

    parser.add_argument(
        "--nostore",
        required=False,
        action="store_true",
        help="Do not Use the store pattern",
    )

    parser.add_argument(
        "--qcheck",
        default=0.5,
        type=float,
        required=False,
        action="store",
        help="Timeout for periodic notification/resampling/replaying check",
    )

    parser.add_argument(
        "--no-timeoffset",
        required=False,
        action="store_true",
        help=(
            "Do not Use TWS/System time offset for non "
            "timestamped prices and to align resampling"
        ),
    )

    parser.add_argument(
        "--data0",
        default=None,
        required=True,
        action="store",
        help="data 0 into the system",
    )

    parser.add_argument(
        "--tradename",
        default=None,
        required=False,
        action="store",
        help="Actual Trading Name of the asset",
    )

    parser.add_argument(
        "--data1",
        default=None,
        required=False,
        action="store",
        help="data 1 into the system",
    )

    parser.add_argument(
        "--timezone",
        default=None,
        required=False,
        action="store",
        help="timezone to get time output into (pytz names)",
    )

    parser.add_argument(
        "--historical",
        required=False,
        action="store_true",
        help="do only historical download",
    )

    parser.add_argument(
        "--fromdate",
        required=False,
        action="store",
        help="Starting date for historical download with format: YYYY-MM-DD[THH:MM:SS]",
    )

    parser.add_argument(
        "--todate",
        required=False,
        action="store",
        help="End date for historical download with format: YYYY-MM-DD[THH:MM:SS]",
    )

    parser.add_argument(
        "--smaperiod",
        default=5,
        type=int,
        required=False,
        action="store",
        help="Period to apply to the Simple Moving Average",
    )

    pgroup = parser.add_mutually_exclusive_group(required=False)

    pgroup.add_argument(
        "--replay",
        required=False,
        action="store_true",
        help="replay to chosen timeframe",
    )

    pgroup.add_argument(
        "--resample",
        required=False,
        action="store_true",
        help="resample to chosen timeframe",
    )

    parser.add_argument(
        "--timeframe",
        default=bt.TimeFrame.Names[0],
        choices=bt.TimeFrame.Names,
        required=False,
        action="store",
        help="TimeFrame for Resample/Replay",
    )

    parser.add_argument(
        "--compression",
        default=1,
        type=int,
        required=False,
        action="store",
        help="Compression for Resample/Replay",
    )

    parser.add_argument(
        "--no-bar2edge",
        required=False,
        action="store_true",
        help="no bar2edge for resample/replay",
    )

    parser.add_argument(
        "--no-adjbartime",
        required=False,
        action="store_true",
        help="no adjbartime for resample/replay",
    )

    parser.add_argument(
        "--no-rightedge",
        required=False,
        action="store_true",
        help="no rightedge for resample/replay",
    )

    parser.add_argument(
        "--broker",
        required=False,
        action="store_true",
        help="Use VisualChart as broker",
    )

    parser.add_argument(
        "--account",
        default=None,
        required=False,
        action="store",
        help="Choose broker account (else first)",
    )

    parser.add_argument(
        "--trade",
        required=False,
        action="store_true",
        help="Do Sample Buy/Sell operations",
    )

    parser.add_argument(
        "--donotsell",
        required=False,
        action="store_true",
        help="Do not sell after a buy",
    )

    parser.add_argument(
        "--exectype",
        default=bt.Order.ExecTypes[0],
        choices=bt.Order.ExecTypes,
        required=False,
        action="store",
        help="Execution to Use when opening position",
    )

    parser.add_argument(
        "--price",
        default=None,
        type=float,
        required=False,
        action="store",
        help="Price in Limit orders or Stop Trigger Price",
    )

    parser.add_argument(
        "--pstoplimit",
        default=None,
        type=float,
        required=False,
        action="store",
        help="Price for the limit in StopLimit",
    )

    parser.add_argument(
        "--stake",
        default=10,
        type=int,
        required=False,
        action="store",
        help="Stake to use in buy operations",
    )

    parser.add_argument(
        "--valid",
        default=None,
        required=False,
        action="store",
        help="Seconds or YYYY-MM-DD",
    )

    parser.add_argument(
        "--cancel",
        default=0,
        type=int,
        required=False,
        action="store",
        help=(
            "Cancel a buy order after n bars in operation,"
            " to be combined with orders like Limit"
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":
    runstrategy()
