"""close-daily.py module.

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
import random

import backtrader as bt
import backtrader.feeds as btfeeds
from backtrader.utils.py3 import with_metaclass

#                        unicode_literals)


class St(bt.Strategy):
""""""
""""""
"""Args::
    order:"""
""""""
    """This data filter simply adds the time given in param ``endtime`` to the
current data datetime
It is intended for daily bars which come from sources with no time
indication and can be used to signal the bar is passed the end of the
session
The default value for ``endtime`` is 1 second before midnight 23:59:59"""

    params = (("endtime", datetime.time(23, 59, 59)),)

    def __call__(self, data):
"""Args::
    data: the data source to filter

Returns::
    - False (always) because this filter does not remove bars from the"""
    - False (always) because this filter does not remove bars from the"""
        # Get time of current (from data source) bar
        dtime = datetime.combine(data.datetime.date(), self.p.endtime)
        data.datetime[0] = data.date2num(dtime)
        return False


def runstrat():
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
        default="../../datas/2005-2006-day-001.txt",
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

    parser.add_argument(
        "--filltime",
        "-ftime",
        default=None,
        required=False,
        help="Add Time to daily bars (HH:MM:SS)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
