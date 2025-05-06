"""stochastic.py module.

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

from . import DivByZero, Highest, Indicator, Lowest, MovAv


class _StochasticBase(Indicator):
""""""
""""""
""""""
""""""
    """By Dr. George Lane in the 50s. It compares a closing price to the price
range and tries to show convergence if the closing prices are close to the
extremes
- It will go up if closing prices are close to the highs
- It will roughly go down if closing prices are close to the lows
It shows divergence if the extremes keep on growing but closing prices
do not in the same manner (distance to the extremes grow)
Formula:
- hh = highest(data.high, period)
- ll = lowest(data.low, period)
- knum = data.close - ll
- kden = hh - ll
- k = 100 * (knum / kden)
- d = MovingAverage(k, period_dfast)
See:
- http://en.wikipedia.org/wiki/Stochastic_oscillator"""

    def __init__(self):
""""""
    """The regular (or slow version) adds an additional moving average layer and
thus:
- The percD line of the StochasticFast becomes the percK line
- percD becomes a  moving average of period_dslow of the original percD
Formula:
- k = k
- d = d
- d = MovingAverage(d, period_dslow)
See:
- http://en.wikipedia.org/wiki/Stochastic_oscillator"""

    alias = ("StochasticSlow",)
    params = (("period_dslow", 3),)

    def _plotlabel(self):
""""""
""""""
    """This version displays the 3 possible lines:
- percK
- percD
- percSlow
Formula:
- k = d
- d = MovingAverage(k, period_dslow)
- dslow =
See:
- http://en.wikipedia.org/wiki/Stochastic_oscillator"""

    lines = ("percDSlow",)
    params = (("period_dslow", 3),)

    plotlines = dict(percDSlow=dict(_name="%DSlow"))

    def _plotlabel(self):
""""""
""""""
        super(StochasticFull, self).__init__()
        self.lines.percK = self.k
        self.lines.percD = self.d
        self.l.percDSlow = self.p.movav(self.l.percD, period=self.p.period_dslow)
