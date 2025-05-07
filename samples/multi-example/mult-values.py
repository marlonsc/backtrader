"""mult-values.py module.

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


class TestSizer(bt.Sizer):
""""""
"""Args::
    comminfo: 
    cash: 
    data: 
    isbuy:"""
    isbuy:"""
        dt, i = self.strategy.datetime.date(), data._id
        s = self.p.stake * (1 + (not isbuy))
        print(
            "{} Data {} OType {} Sizing to {}".format(
                dt, data._name, ("buy" * isbuy) or "sell", s
            )
        )

        return s


class St(bt.Strategy):
""""""
"""Args::
    order:"""
""""""
""""""
"""Args::
    args: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Multiple Values and Brackets",
    )

    parser.add_argument(
        "--data0",
        default="../../datas/nvda-1999-2014.txt",
        required=False,
        help="Data0 to read in",
    )

    parser.add_argument(
        "--data1",
        default="../../datas/yhoo-1996-2014.txt",
        required=False,
        help="Data1 to read in",
    )

    parser.add_argument(
        "--data2",
        default="../../datas/orcl-1995-2014.txt",
        required=False,
        help="Data1 to read in",
    )

    # Defaults for dates
    parser.add_argument(
        "--fromdate",
        required=False,
        default="2001-01-01",
        help="Date[time] in YYYY-MM-DD[THH:MM:SS] format",
    )

    parser.add_argument(
        "--todate",
        required=False,
        default="2007-01-01",
        help="Date[time] in YYYY-MM-DD[THH:MM:SS] format",
    )

    parser.add_argument(
        "--cerebro",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--broker",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--sizer",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--strat",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--plot",
        required=False,
        default="",
        nargs="?",
        const="{}",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    return parser.parse_args(pargs)


if __name__ == "__main__":
    runstrat()
