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

from collections import OrderedDict

from backtrader import Analyzer
from backtrader.utils.py3 import range


class AnnualReturn(Analyzer):
    """This analyzer calculates the AnnualReturns by looking at the beginning
    and end of the year


    """

    def stop(self):
        """ """
        # Must have stats.broker
        cur_year = -1

        value_start = 0.0
        value_cur = 0.0
        value_end = 0.0

        self.rets = list()
        self.ret = OrderedDict()

        for i in range(len(self.data) - 1, -1, -1):
            dt = self.data.datetime.date(-i)
            value_cur = self.strategy.stats.broker.value[-i]

            if dt.year > cur_year:
                if cur_year >= 0:
                    annualret = round(((value_end / value_start) - 1.0), 6)
                    self.rets.append(annualret)
                    self.ret[cur_year] = annualret

                    # changing between real years, use last value as new start
                    value_start = value_end
                else:
                    # No value set whatsoever, use the currently loaded value
                    value_start = value_cur

                cur_year = dt.year

            # No matter what, the last value is always the last loaded value
            value_end = value_cur

        if cur_year not in self.ret:
            # finish calculating pending data
            try:
                annualret = (value_end / value_start) - 1.0
            except ZeroDivisionError:
                annualret = float("-inf")

            self.rets.append(annualret)
            self.ret[cur_year] = round(annualret, 6)

    def get_analysis(self):
        """ """
        return self.ret
