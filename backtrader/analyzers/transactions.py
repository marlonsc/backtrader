"""transactions.py module.

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

import collections

import backtrader as bt
from backtrader import Order, Position


class Transactions(bt.Analyzer):
"""This analyzer reports the transactions occurred with each an every data in
the system
It looks at the order execution bits to create a ``Position`` starting from
0 during each ``next`` cycle.
The result is used during next to record the transactions

Returns::
    each return as keys"""
    each return as keys"""

    params = (
        ("headers", False),
        ("_pfheaders", ("date", "amount", "price", "sid", "symbol", "value")),
    )

    def start(self):
""""""
"""Args::
    order:"""
""""""
        # super(Transactions, self).next()  # let dtkey update
        entries = []
        for i, dname in self._idnames:
            pos = self._positions.get(dname, None)
            if pos is not None:
                size, price = pos.size, pos.price
                if size:
                    entries.append([size, price, i, dname, -size * price])

        if entries:
            self.rets[self.strategy.datetime.datetime()] = entries

        self._positions.clear()
