"""btfd.py module.

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

# References:
#  - https://www.reddit.com/r/algotrading/comments/5jez2b/can_anyone_replicate_this_strategy/
#  - http://dark-bid.com/BTFD-only-strategy-that-matters.html


class ValueUnlever(bt.observers.Value):
    """Extension of regular Value observer to add leveraged view"""

    lines = ("value_lever", "asset")
    params = (
        ("assetstart", 100000.0),
        ("lever", True),
    )

    def next(self):
""""""
""""""
""""""
""""""
""""""
"""Args::
    order:"""
"""Args::
    trade:"""
"""Args::
    args: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=" - ".join(
            [
                "BTFD",
                "http://dark-bid.com/BTFD-only-strategy-that-matters.html",
                (
                    "https://www.reddit.com/r/algotrading/comments/5jez2b/"
                    "can_anyone_replicate_this_strategy/"
                ),
            ]
        ),
    )

    parser.add_argument(
        "--offline",
        required=False,
        action="store_true",
        help="Use offline file with ticker name",
    )

    parser.add_argument(
        "--data",
        required=False,
        default="^GSPC",
        metavar="TICKER",
        help="Yahoo ticker to download",
    )

    parser.add_argument(
        "--fromdate",
        required=False,
        default="1990-01-01",
        metavar="YYYY-MM-DD[THH:MM:SS]",
        help="Starting date[time]",
    )

    parser.add_argument(
        "--todate",
        required=False,
        default="2016-10-01",
        metavar="YYYY-MM-DD[THH:MM:SS]",
        help="Ending date[time]",
    )

    parser.add_argument(
        "--cerebro",
        required=False,
        default="stdstats=False",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--broker",
        required=False,
        default="cash=100000.0, coc=True",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--valobserver",
        required=False,
        default="assetstart=100000.0",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--strat",
        required=False,
        default='approach="highlow"',
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--comminfo",
        required=False,
        default="leverage=2.0",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--plot",
        required=False,
        default="",
        nargs="?",
        const="volume=False",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    return parser.parse_args(pargs)


if __name__ == "__main__":
    runstrat()
