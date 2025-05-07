"""close-minute.py module.

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
import datetime

import backtrader as bt
import backtrader.feeds as btfeeds

#                        unicode_literals)


class St(bt.Strategy):
""""""
""""""
"""Args::
    order:"""
""""""
""""""
"""Args::
    args:"""
""""""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for Close Orders with daily data",
    )

    parser.add_argument(
        "--infile",
        "-i",
        required=False,
        default="../../datas/2006-min-005.txt",
        help="File to be read in",
    )

    parser.add_argument(
        "--csvformat",
        "-c",
        required=False,
        default="bt",
        choices=[
            "bt",
            "visualchart",
            "sierrachart",
            "yahoo",
            "yahoo_unreversed",
        ],
        help="CSV Format",
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        required=False,
        default=None,
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        required=False,
        default=None,
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--eosbar",
        required=False,
        action="store_true",
        help="Consider a bar with the end of session time tobe the end of the session",
    )

    parser.add_argument(
        "--tend",
        "-te",
        default=None,
        required=False,
        help="End time for the Session Filter (HH:MM)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
