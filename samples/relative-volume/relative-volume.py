"""relative-volume.py module.

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
import backtrader.feeds as btfeeds
from relvolbybar import RelativeVolumeByBar


def runstrategy():
""""""
""""""
    parser = argparse.ArgumentParser(description="MultiData Strategy")

    parser.add_argument(
        "--data",
        "-d",
        default="../../datas/2006-01-02-volume-min-001.txt",
        help="data to add to the system",
    )

    parser.add_argument(
        "--prestart", default="08:00", help="Start time for the Session Filter"
    )

    parser.add_argument(
        "--start", default="09:15", help="Start time for the Session Filter"
    )

    parser.add_argument(
        "--end", "-te", default="17:15", help="End time for the Session Filter"
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
        "--writer", "-w", action="store_true", help="Add a writer to cerebro"
    )

    parser.add_argument(
        "--wrcsv",
        "-wc",
        action="store_true",
        help="Enable CSV Output in the writer",
    )

    parser.add_argument("--plot", "-p", action="store_true", help="Plot the read data")

    parser.add_argument("--numfigs", "-n", default=1, help="Plot using numfigs figures")

    return parser.parse_args()


if __name__ == "__main__":
    runstrategy()
