#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Added by: @baobach (2024)
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

import math

from backtrader import Analyzer, TimeFrame
from backtrader.analyzers import TimeReturn
from backtrader.mathsupport import average, standarddev
from backtrader.utils.py3 import itervalues


class SortinoRatio(Analyzer):
    """This analyzer calculates the Sortino Ratio of a strategy using a risk free
asset which is simply an interest rate
See also:
- https://en.wikipedia.org/wiki/Sortino_ratio"""

    params = (
        ("timeframe", TimeFrame.Years),
        ("compression", 1),
        ("riskfreerate", 0.00),
        ("factor", None),
        ("convertrate", True),
        ("annualize", False),
        ("stddev_sample", False),
        ("daysfactor", None),
        ("legacyannual", False),
        ("fund", None),
    )

    RATEFACTORS = {
        TimeFrame.Days: 252,
        TimeFrame.Weeks: 52,
        TimeFrame.Months: 12,
        TimeFrame.Years: 1,
    }

    def __init__(self):
        """ """
        self.timereturn = TimeReturn(
            timeframe=self.p.timeframe,
            compression=self.p.compression,
            fund=self.p.fund,
        )

    def stop(self):
        """ """
        super(SortinoRatio, self).stop()
        ret_free_avg = None
        retdev = None

        # Get the returns from the subanalyzer
        returns = list(itervalues(self.timereturn.get_analysis()))

        rate = self.p.riskfreerate

        factor = None

        if self.p.factor is not None:
            factor = self.p.factor  # user specified factor
        elif self.p.timeframe in self.RATEFACTORS:
            # Get the conversion factor from the default table
            factor = self.RATEFACTORS[self.p.timeframe]

        if factor is not None:
            # A factor was found

            if self.p.convertrate:
                # Standard: downgrade annual returns to timeframe factor
                rate = pow(1.0 + rate, 1.0 / factor) - 1.0
            else:
                # Else upgrade returns to yearly returns
                returns = [pow(1.0 + x, factor) - 1.0 for x in returns]

        lrets = len(returns) - self.p.stddev_sample
        # Check if the ratio can be calculated
        if lrets:
            # Get the excess returns
            ret_free = [r - rate for r in returns]
            ret_free_avg = average(ret_free)
            try:
                # Calculate downside deviation
                downside_returns = [x for x in ret_free if x < 0]
                retdev = standarddev(
                    downside_returns,
                    avgx=ret_free_avg,
                    bessel=self.p.stddev_sample,
                )

                ratio = ret_free_avg / retdev

                if factor is not None and self.p.convertrate and self.p.annualize:
                    ratio = math.sqrt(factor) * ratio
            except (ValueError, TypeError, ZeroDivisionError):
                ratio = None
        else:
            # no returns or stddev_sample was active and 1 return
            ratio = None

        self.ratio = ratio

        self.rets["sortinoratio"] = self.ratio
        self.rets["ret_free_avg"] = ret_free_avg
        self.rets["retdev"] = retdev
