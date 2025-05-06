"""bidask.py module.

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


class BidAskCSV(btfeeds.GenericCSVData):
""""""
""""""
""""""
""""""
""""""
""""""
    args = parse_args()

    cerebro = bt.Cerebro()  # Create a cerebro

    data = BidAskCSV(dataname=args.data, dtformat=args.dtformat)
    cerebro.adddata(data)  # Add the 1st data to cerebro
    # Add the strategy to cerebro
    cerebro.addstrategy(St, sma=args.sma, period=args.period)
    cerebro.run()


if __name__ == "__main__":
    runstrategy()
