"""ibtest.py module.

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
        description="Test Interactive Brokers integration",
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
        "--usestore",
        required=False,
        action="store_true",
        help="Use the store pattern",
    )

    parser.add_argument(
        "--notifyall",
        required=False,
        action="store_true",
        help="Notify all messages to strategy as store notifs",
    )

    parser.add_argument(
        "--debug",
        required=False,
        action="store_true",
        help="Display all info received form IB",
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        required=False,
        action="store",
        help="Host for the Interactive Brokers TWS Connection",
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
        "--port",
        default=7496,
        type=int,
        required=False,
        action="store",
        help="Port for the Interactive Brokers TWS Connection",
    )

    parser.add_argument(
        "--clientId",
        default=None,
        type=int,
        required=False,
        action="store",
        help="Client Id to connect to TWS (default: random)",
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
        "--reconnect",
        default=3,
        type=int,
        required=False,
        action="store",
        help="Number of recconnection attempts to TWS",
    )

    parser.add_argument(
        "--timeout",
        default=3.0,
        type=float,
        required=False,
        action="store",
        help="Timeout between reconnection attempts to TWS",
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
        "--what",
        default=None,
        required=False,
        action="store",
        help="specific price type for historical requests",
    )

    parser.add_argument(
        "--no-backfill_start",
        required=False,
        action="store_true",
        help="Disable backfilling at the start",
    )

    parser.add_argument(
        "--latethrough",
        required=False,
        action="store_true",
        help=(
            "if resampling replaying, adjusting time "
            "and disabling time offset, let late samples "
            "through"
        ),
    )

    parser.add_argument(
        "--no-backfill",
        required=False,
        action="store_true",
        help="Disable backfilling after a disconnection",
    )

    parser.add_argument(
        "--rtbar",
        default=False,
        required=False,
        action="store_true",
        help="Use 5 seconds real time bar updates if possible",
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
        help=(
            "resample/replay, do not accept late samples "
            "in new bar if the data source let them through "
            "(latethrough)"
        ),
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
        "--broker", required=False, action="store_true", help="Use IB as broker"
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
        type=int,
        required=False,
        action="store",
        help="Seconds to keep the order alive (0 means DAY)",
    )

    pgroup = parser.add_mutually_exclusive_group(required=False)
    pgroup.add_argument(
        "--stoptrail",
        required=False,
        action="store_true",
        help="Issue a stoptraillimit after buy( do not sell",
    )

    pgroup.add_argument(
        "--traillimit",
        required=False,
        action="store_true",
        help="Issue a stoptrail after buying (do not sell",
    )

    pgroup.add_argument(
        "--oca",
        required=False,
        action="store_true",
        help="Test oca by putting 2 orders in a group",
    )

    pgroup.add_argument(
        "--bracket",
        required=False,
        action="store_true",
        help="Test bracket orders by issuing high/low sides",
    )

    pgroup = parser.add_mutually_exclusive_group(required=False)
    pgroup.add_argument(
        "--trailamount",
        default=None,
        type=float,
        required=False,
        action="store",
        help="trailamount for StopTrail order",
    )

    pgroup.add_argument(
        "--trailpercent",
        default=None,
        type=float,
        required=False,
        action="store",
        help="trailpercent for StopTrail order",
    )

    parser.add_argument(
        "--limitoffset",
        default=None,
        type=float,
        required=False,
        action="store",
        help="limitoffset for StopTrailLimit orders",
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
