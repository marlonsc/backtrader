"""oandatest.py module.

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

StoreCls = bt.stores.OandaStore
DataCls = bt.feeds.OandaData
# BrokerCls = bt.brokers.OandaBroker


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
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Test Oanda integration",
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
        "--stopafter",
        default=0,
        type=int,
        required=False,
        action="store",
        help="Stop after x lines of LIVE data",
    )

    parser.add_argument(
        "--no-store",
        required=False,
        action="store_true",
        help="Do not use the store pattern",
    )

    parser.add_argument(
        "--debug",
        required=False,
        action="store_true",
        help="Display all info received from source",
    )

    parser.add_argument(
        "--token",
        default=None,
        required=True,
        action="store",
        help="Access token to use",
    )

    parser.add_argument(
        "--account",
        default=None,
        required=True,
        action="store",
        help="Account identifier to use",
    )

    parser.add_argument(
        "--live",
        default=None,
        required=False,
        action="store",
        help="Go to live server rather than practice",
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
        "--data0",
        default=None,
        required=True,
        action="store",
        help="data 0 into the system",
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
        "--bidask",
        default=None,
        required=False,
        action="store_true",
        help="Use bidask ... if False use midpoint",
    )

    parser.add_argument(
        "--useask",
        default=None,
        required=False,
        action="store_true",
        help='Use the "ask" of bidask prices/streaming',
    )

    parser.add_argument(
        "--no-backfill_start",
        required=False,
        action="store_true",
        help="Disable backfilling at the start",
    )

    parser.add_argument(
        "--no-backfill",
        required=False,
        action="store_true",
        help="Disable backfilling after a disconnection",
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
        default=bt.TimeFrame.Names[1],
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
        "--timeframe1",
        default=None,
        choices=bt.TimeFrame.Names,
        required=False,
        action="store",
        help="TimeFrame for Resample/Replay - Data1",
    )

    parser.add_argument(
        "--compression1",
        default=None,
        type=int,
        required=False,
        action="store",
        help="Compression for Resample/Replay - Data1",
    )

    parser.add_argument(
        "--no-takelate",
        required=False,
        action="store_true",
        help="resample/replay, do not accept late samples",
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
        help="Use Oanda as broker",
    )

    parser.add_argument(
        "--trade",
        required=False,
        action="store_true",
        help="Do Sample Buy/Sell operations",
    )

    parser.add_argument(
        "--sell", required=False, action="store_true", help="Start by selling"
    )

    parser.add_argument(
        "--usebracket",
        required=False,
        action="store_true",
        help="Test buy_bracket",
    )

    parser.add_argument(
        "--donotcounter",
        required=False,
        action="store_true",
        help="Do not counter the 1st operation",
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
        type=float,
        required=False,
        action="store",
        help="Seconds to keep the order alive (0 means DAY)",
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
            "For example (escape the quotes if needed):\n"
            "\n"
            '  --plot style="candle" (to plot candles)\n'
        ),
    )

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == "__main__":
    runstrategy()
