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

from . import TimeReturn


class Benchmark(TimeReturn):
    """This observer stores the *returns* of the strategy and the *return* of a
    reference asset which is one of the datas passed to the system.


    """

    _stclock = True

    lines = ("benchmark",)
    plotlines = dict(benchmark=dict(_name="Benchmark"))

    params = (
        ("data", None),
        ("_doprenext", False),
        # Set to false to ensure the asset is measured at 0% in the 1st tick
        ("firstopen", False),
        ("fund", None),
    )

    def _plotlabel(self):
        """ """
        labels = super(Benchmark, self)._plotlabel()
        labels.append(self.p.data._name)
        return labels

    def __init__(self):
        """ """
        if self.p.data is None:  # use the 1st data in the system if none given
            self.p.data = self.data0

        super(Benchmark, self).__init__()  # treturn including data parameter
        # Create a time return object without the data
        kwargs = self.p._getkwargs()
        kwargs.update(data=None)  # to create a return for the strategy
        t = self._owner._addanalyzer_slave(bt.analyzers.TimeReturn, **kwargs)

        # swap for consistency
        self.treturn, self.tbench = t, self.treturn

    def next(self):
        """ """
        super(Benchmark, self).next()
        self.lines.benchmark[0] = self.tbench.rets.get(self.treturn.dtkey, float("NaN"))

    def prenext(self):
        """ """
        if self.p._doprenext:
            super(TimeReturn, self).prenext()
