"""memory-savings.py module.

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

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
import backtrader.utils.flushfile


class TestInd(bt.Indicator):
""""""
""""""
""""""
""""""
""""""
"""Args::
    msg:"""
""""""
"""Args::
    ind: 
    i: 
    deep:"""
    deep:"""
        tind = 0
        for line in ind.lines:
            tind += len(line.array)
            tline = len(line.array)

        tsub = 0
        for j, sind in enumerate(ind.getindicators()):
            tsub += self.rindicator(sind, j, deep + 1)

        iname = ind.__class__.__name__.split(".")[-1]

        logtxt = "---- Indicator {}.{} {} Total Cells {} - Cells per line {}"
        self.loglendetails(logtxt.format(deep, i, iname, tind, tline))
        logtxt = "---- SubIndicators Total Cells {}"
        self.loglendetails(logtxt.format(deep, i, iname, tsub))

        return tind + tsub


def runstrat():
""""""
""""""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Check Memory Savings",
    )

    parser.add_argument(
        "--data",
        required=False,
        default="../../datas/yhoo-1996-2015.txt",
        help="Data to be read in",
    )

    parser.add_argument(
        "--save",
        required=False,
        type=int,
        default=0,
        help="Memory saving level [1, 0, -1, -2]",
    )

    parser.add_argument(
        "--datalines",
        required=False,
        action="store_true",
        help="Print data lines",
    )

    parser.add_argument(
        "--lendetails",
        required=False,
        action="store_true",
        help="Print individual items memory usage",
    )

    parser.add_argument(
        "--plot", required=False, action="store_true", help="Plot the result"
    )

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
