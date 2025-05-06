"""sharpe.py module.

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

import math

from backtrader import Analyzer, TimeFrame
from backtrader.analyzers import AnnualReturn, TimeReturn
from backtrader.mathsupport import average, standarddev
from backtrader.utils.py3 import itervalues


class SharpeRatio(Analyzer):
    """This analyzer calculates the SharpeRatio of a strategy using a risk free
asset which is simply an interest rate
See also:
- https://en.wikipedia.org/wiki/Sharpe_ratio"""

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
""""""
""""""
        """Optimizies the object if optreturn is in effect"""
        super().optimize()

        self.timereturn.optimize()


class SharpeRatio_A(SharpeRatio):
    """Extension of the SharpeRatio which returns the Sharpe Ratio directly in
annualized form
The following param has been changed from ``SharpeRatio``
- ``annualize`` (default: ``True``)"""

    params = (("annualize", True),)
