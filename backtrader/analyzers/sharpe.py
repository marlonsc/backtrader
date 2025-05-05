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

import math

from backtrader import Analyzer, TimeFrame
from backtrader.analyzers import AnnualReturn, TimeReturn
from backtrader.mathsupport import average, standarddev
from backtrader.utils.py3 import itervalues


class SharpeRatio(Analyzer):
    """This analyzer calculates the SharpeRatio of a strategy using a risk free
    asset which is simply an interest rate

    See also:

      - https://en.wikipedia.org/wiki/Sharpe_ratio


    """

    params = (
        ("timeframe", TimeFrame.Years),
        ("compression", 1),
        ("riskfreerate", 0.01),
        ("factor", None),
        ("convertrate", True),
        ("annualize", False),
        ("stddev_sample", False),
        # old behavior
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
        if self.p.legacyannual:
            self.anret = AnnualReturn()
        else:
            self.timereturn = TimeReturn(
                timeframe=self.p.timeframe,
                compression=self.p.compression,
                fund=self.p.fund,
            )

    def stop(self):
        """ """
        super(SharpeRatio, self).stop()
        ret_free_avg = None
        retdev = None

        if self.p.legacyannual:
            rate = self.p.riskfreerate
            retavg = average([r - rate for r in self.anret.rets])
            retdev = standarddev(self.anret.rets)

            self.ratio = retavg / retdev
        else:
            # Get the returns from the subanalyzer
            returns = list(itervalues(self.timereturn.get_analysis()))

            rate = self.p.riskfreerate  #

            factor = None

            # Hack to identify old code
            if self.p.timeframe == TimeFrame.Days and self.p.daysfactor is not None:
                factor = self.p.daysfactor

            else:
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
                # Get the excess returns - arithmetic mean - original sharpe
                ret_free = [r - rate for r in returns]
                ret_free_avg = average(ret_free)
                retdev = standarddev(
                    ret_free, avgx=ret_free_avg, bessel=self.p.stddev_sample
                )

                try:
                    ratio = ret_free_avg / retdev

                    if factor is not None and self.p.convertrate and self.p.annualize:
                        ratio = math.sqrt(factor) * ratio
                except (ValueError, TypeError, ZeroDivisionError):
                    ratio = None
            else:
                # no returns or stddev_sample was active and 1 return
                ratio = None

            self.ratio = ratio

            self.rets["sharperatio"] = (
                round(self.ratio, 4) if self.ratio else self.ratio
            )
        self.rets["ret_free_avg"] = ret_free_avg
        self.rets["retdev"] = retdev

    def optimize(self):
        """Optimizies the object if optreturn is in effect"""
        super().optimize()

        self.timereturn.optimize()


class SharpeRatio_A(SharpeRatio):
    """Extension of the SharpeRatio which returns the Sharpe Ratio directly in
    annualized form

    The following param has been changed from ``SharpeRatio``

      - ``annualize`` (default: ``True``)


    """

    params = (("annualize", True),)
