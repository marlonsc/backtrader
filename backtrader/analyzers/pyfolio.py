"""pyfolio.py module.

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

import backtrader as bt
from backtrader.utils.py3 import iteritems

from . import GrossLeverage, PositionsValue, TimeReturn, Transactions


class PyFolio(bt.Analyzer):
"""This analyzer uses 4 children analyzers to collect data and transforms it
in to a data set compatible with ``pyfolio``
Children Analyzer
- ``TimeReturn``
Used to calculate the returns of the global portfolio value
- ``PositionsValue``
Used to calculate the value of the positions per data. It sets the
``headers`` and ``cash`` parameters to ``True``
- ``Transactions``
Used to record each transaction on a data (size, price, value). Sets
the ``headers`` parameter to ``True``
- ``GrossLeverage``
Keeps track of the gross leverage (how much the strategy is invested)

Returns::
    each return as keys"""
    each return as keys"""

    params = (("timeframe", bt.TimeFrame.Days), ("compression", 1))

    def __init__(self):
""""""
""""""
        """Returns a tuple of 4 elements which can be used for further processing with
``pyfolio``
returns, positions, transactions, gross_leverage
Because the objects are meant to be used as direct input to ``pyfolio``
this method makes a local import of ``pandas`` to convert the internal
*backtrader* results to *pandas DataFrames* which is the expected input
by, for example, ``pyfolio.create_full_tear_sheet``
The method will break if ``pandas`` is not installed"""
        # keep import local to avoid disturbing installations with no pandas
        import pandas
        from pandas import DataFrame as DF

        #
        # Returns
        cols = ["index", "return"]
        returns = DF.from_records(
            iteritems(self.rets["returns"]), index=cols[0], columns=cols
        )
        returns.index = pandas.to_datetime(returns.index)
        returns.index = returns.index.tz_localize("UTC")
        rets = returns["return"]
        #
        # Positions
        pss = self.rets["positions"]
        ps = [[k] + v[-2:] for k, v in iteritems(pss)]
        cols = ps.pop(0)  # headers are in the first entry
        positions = DF.from_records(ps, index=cols[0], columns=cols)
        positions.index = pandas.to_datetime(positions.index)
        positions.index = positions.index.tz_localize("UTC")

        #
        # Transactions
        txss = self.rets["transactions"]
        txs = list()
        # The transactions have a common key (date) and can potentially happend
        # for several assets. The dictionary has a single key and a list of
        # lists. Each sublist contains the fields of a transaction
        # Hence the double loop to undo the list indirection
        for k, v in iteritems(txss):
            for v2 in v:
                txs.append([k] + v2)

        cols = txs.pop(0)  # headers are in the first entry
        transactions = DF.from_records(txs, index=cols[0], columns=cols)
        transactions.index = pandas.to_datetime(transactions.index)
        transactions.index = transactions.index.tz_localize("UTC")

        # Gross Leverage
        cols = ["index", "gross_lev"]
        gross_lev = DF.from_records(
            iteritems(self.rets["gross_lev"]), index=cols[0], columns=cols
        )

        gross_lev.index = pandas.to_datetime(gross_lev.index)
        gross_lev.index = gross_lev.index.tz_localize("UTC")
        glev = gross_lev["gross_lev"]

        # Return all together
        return rets, positions, transactions, glev
