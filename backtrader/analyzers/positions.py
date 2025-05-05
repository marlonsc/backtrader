#!/usr/bin/env python
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


class PositionsValue(bt.Analyzer):
    """This analyzer reports the value of the positions of the current set of
    datas


    :returns: each return as keys

    """

    params = (
        ("headers", False),
        ("cash", False),
    )

    def start(self):
        """ """
        if self.p.headers:
            headers = [d._name or "Data%d" % i for i, d in enumerate(self.datas)]
            self.rets["Datetime"] = headers + ["cash"] * self.p.cash

        tf = min(d._timeframe for d in self.datas)
        self._usedate = tf >= bt.TimeFrame.Days

    def next(self):
        """ """
        pvals = [self.strategy.broker.get_value([d]) for d in self.datas]
        if self.p.cash:
            pvals.append(self.strategy.broker.get_cash())

        if self._usedate:
            self.rets[self.strategy.datetime.date()] = pvals
        else:
            self.rets[self.strategy.datetime.datetime()] = pvals
