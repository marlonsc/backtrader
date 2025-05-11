#!/usr/bin/env python
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

from backtrader.indicator import Indicator
from .basicops import Highest, Lowest
from .smma import SmoothedMovingAverage


class TrueHigh(Indicator):
    """Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in Technical
    Trading Systems"* for the ATR.

    Records the "true high" which is the maximum of today's high and
    yesterday's close

    Formula:
      - truehigh = max(high, close_prev)

    See:
      - http://en.wikipedia.org/wiki/Average_true_range
    """

    lines = ("truehigh",)

    def __init__(self, *args, **kwargs):
        self.lines.truehigh = Highest(data=self.data.high, period=1)
        super().__init__(*args, **kwargs)


class TrueLow(Indicator):
    """Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in Technical
    Trading Systems"* for the ATR.

    Records the "true low" which is the minimum of today's low and
    yesterday's close

    Formula:
      - truelow = min(low, close_prev)

    See:
      - http://en.wikipedia.org/wiki/Average_true_range
    """

    lines = ("truelow",)

    def __init__(self, *args, **kwargs):
        self.lines.truelow = Lowest(data=self.data.low, period=1)
        super().__init__(*args, **kwargs)


class TrueRange(Indicator):
    """Defined by J. Welles Wilder, Jr. in 1978 in his book New Concepts in Technical
    Trading Systems.

    Formula:
      - max(high - low, abs(high - prev_close), abs(prev_close - low)

      which can be simplified to

      - max(high, prev_close) - min(low, prev_close)

    See:
      - http://en.wikipedia.org/wiki/Average_true_range

    The idea is to take the previous close into account to calculate the range
    if it yields a larger range than the daily range (High - Low)
    """

    alias = ("TR",)

    lines = ("tr",)

    def __init__(self, *args, **kwargs):
        self.lines.tr = TrueHigh(data=self.data) - TrueLow(data=self.data)
        super().__init__(*args, **kwargs)


class AverageTrueRange(Indicator):
    """Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in Technical
    Trading Systems"*.

    The idea is to take the close into account to calculate the range if it
    yields a larger range than the daily range (High - Low)

    Formula:
      - SmoothedMovingAverage(TrueRange, period)

    See:
      - http://en.wikipedia.org/wiki/Average_true_range
    """

    alias = ("ATR",)

    lines = ("atr",)
    params = (("period", 14), ("movav", SmoothedMovingAverage))

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.movav] * self.p.notdefault("movav")
        return plabels

    def __init__(self, *args, **kwargs):
        self.lines.atr = self.p.movav(TrueRange(data=self.data), period=self.p.period)
        super().__init__(*args, **kwargs)

ATR = AverageTrueRange
