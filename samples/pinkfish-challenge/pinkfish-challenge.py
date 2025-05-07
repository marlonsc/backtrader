"""pinkfish-challenge.py module.

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
import backtrader.indicators as btind


class DayStepsCloseFilter(bt.with_metaclass(bt.MetaParams, object)):
    """Replays a bar in 2 steps:
- In the 1st step the "Open-High-Low" could be evaluated to decide if to
act on the close (the close is still there ... should not be evaluated)
- If a "Close" order has been executed
In this 1st fragment the "Close" is replaced through the "open" althoug
other alternatives would be possible like high - low average, or an
algorithm based on where the "close" ac
and
- Open-High-Low-Close"""

    params = (("cvol", 0.5),)  # 0 -> 1 amount of volume to keep for close

    def __init__(self, data):
"""Args::
    data:"""
"""Args::
    data:"""
"""Called when the data is no longer producing bars
Can be called multiple times. It has the chance to (for example)
produce extra bars

Args::
    data:"""
    data:"""
        if self.pendingbar is not None:
            data.backwards()  # remove delivered open bar
            data._add2stack(self.pendingbar)  # add remaining
            self.pendingbar = None  # No further action
            return True  # something delivered

        return False  # nothing delivered here


class DayStepsReplayFilter(bt.with_metaclass(bt.MetaParams, object)):
    """Replays a bar in 2 steps:
- In the 1st step the "Open-High-Low" could be evaluated to decide if to
act on the close (the close is still there ... should not be evaluated)
- If a "Close" order has been executed
In this 1st fragment the "Close" is replaced through the "open" althoug
other alternatives would be possible like high - low average, or an
algorithm based on where the "close" ac
and
- Open-High-Low-Close"""

    params = (("closevol", 0.5),)  # 0 -> 1 amount of volume to keep for close

    # replaying = True

    def __init__(self, data):
"""Args::
    data:"""
"""Args::
    data:"""
""""""
""""""
""""""
"""Args::
    order:"""
""""""
""""""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for pinkfish challenge",
    )

    parser.add_argument(
        "--data",
        required=False,
        default="../../datas/yhoo-1996-2015.txt",
        help="Data to be read in",
    )

    parser.add_argument(
        "--fromdate",
        required=False,
        default="2005-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        required=False,
        default="2006-12-31",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--cash",
        required=False,
        action="store",
        type=float,
        default=50000,
        help="Cash to start with",
    )

    parser.add_argument(
        "--sellafter",
        required=False,
        action="store",
        type=int,
        default=2,
        help="Sell after so many bars in market",
    )

    parser.add_argument(
        "--highperiod",
        required=False,
        action="store",
        type=int,
        default=20,
        help="Period to look for the highest",
    )

    parser.add_argument(
        "--no-replay",
        required=False,
        action="store_true",
        help="Use Replay + replay filter",
    )

    parser.add_argument(
        "--market",
        required=False,
        action="store_true",
        help="Use Market exec instead of Close",
    )

    parser.add_argument(
        "--oldbuysell",
        required=False,
        action="store_true",
        help="Old buysell plot behavior - ON THE PRICE",
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
    runstrat()
