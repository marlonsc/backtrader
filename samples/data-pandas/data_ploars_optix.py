# -*- coding: UTF-8 -*-

# import

# globals

# functions
#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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
import polars as pl


class PolarsDataOptix(btfeeds.PandasData):
    """ """

    lines = (
        "optix_close",
        "optix_pess",
        "optix_opt",
    )
    params = (("optix_close", -1), ("optix_pess", -1), ("optix_opt", -1))

    if False:
        # No longer needed with version 1.9.62.122
        datafields = btfeeds.PandasData.datafields + (
            ["optix_close", "optix_pess", "optix_opt"]
        )


class StrategyOptix(bt.Strategy):
    """ """

    def next(self):
        """ """
        print(
            "%03d %f %f, %f"
            % (
                len(self),
                self.data.optix_close[0],
                self.data.lines.optix_pess[0],
                self.data.optix_opt[0],
            )
        )


def runstrat():
    """ """
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Add a strategy
    cerebro.addstrategy(StrategyOptix)

    # Get a polars dataframe
    datapath = "../../datas/2006-day-001-optix.txt"

    # Simulate the header row isn't there if noheaders requested
    skiprows = 1 if args.noheaders else 0
    None if args.noheaders else 0

    dataframe = pl.read_csv(
        datapath,
        skip_rows=skiprows,
        has_header=not args.noheaders,
        parse_dates=True,
    )

    if not args.noprint:
        print("--------------------------------------------------")
        print(dataframe)
        print("--------------------------------------------------")

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = PolarsDataOptix(dataname=dataframe.to_pandas())

    cerebro.adddata(data)

    # Run over everything
    cerebro.run()

    # Plot the result
    if not args.noplot:
        cerebro.plot(style="bar")


def parse_args():
    """ """
    parser = argparse.ArgumentParser(description="Polars test script")

    parser.add_argument(
        "--noheaders",
        action="store_true",
        default=False,
        required=False,
        help="Do not use header rows",
    )

    parser.add_argument(
        "--noprint",
        action="store_true",
        default=False,
        help="Print the dataframe",
    )

    parser.add_argument(
        "--noplot",
        action="store_true",
        default=False,
        help="Do not plot the chart",
    )

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
