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

from . import PeriodN

__all__ = ["OLS_Slope_InterceptN", "OLS_TransformationN", "OLS_BetaN", "CointN"]


class OLS_Slope_InterceptN(PeriodN):
    """Calculates a linear regression using ``statsmodel.OLS`` (Ordinary least
    squares) of data1 on data0

    Uses ``pandas`` and ``statsmodels``


    """

    _mindatas = 2  # ensure at least 2 data feeds are passed

    packages = (
        ("pandas", "pd"),
        ("statsmodels.api", "sm"),
    )
    lines = (
        "slope",
        "intercept",
    )
    params = (("period", 10),)

    def next(self):
        """ """
        p0 = pd.Series(self.data0.get(size=self.p.period))
        p1 = pd.Series(self.data1.get(size=self.p.period))
        p1 = sm.add_constant(p1)
        intercept, slope = sm.OLS(p0, p1).fit().params

        self.lines.slope[0] = slope
        self.lines.intercept[0] = intercept


class OLS_TransformationN(PeriodN):
    """Calculates the ``zscore`` for data0 and data1. Although it doesn't directly
    uses any external package it relies on ``OLS_SlopeInterceptN`` which uses
    ``pandas`` and ``statsmodels``


    """

    _mindatas = 2  # ensure at least 2 data feeds are passed
    lines = (
        "spread",
        "spread_mean",
        "spread_std",
        "zscore",
    )
    params = (("period", 10),)

    def __init__(self):
        """ """
        slint = OLS_Slope_InterceptN(*self.datas)

        spread = self.data0 - (slint.slope * self.data1 + slint.intercept)
        self.l.spread = spread

        self.l.spread_mean = bt.ind.SMA(spread, period=self.p.period)
        self.l.spread_std = bt.ind.StdDev(spread, period=self.p.period)
        self.l.zscore = (spread - self.l.spread_mean) / self.l.spread_std


class OLS_BetaN(PeriodN):
    """Calculates a regression of data1 on data0 using ``statsmodels.api.ols``

    Uses ``pandas`` and ``statsmodels``


    """

    _mindatas = 2  # ensure at least 2 data feeds are passed

    packages = (
        ("pandas", "pd"),
        ("statsmodels.api", "smapi"),
    )

    lines = ("beta",)
    params = (("period", 10),)

    def next(self):
        """ """
        y, x = (pd.Series(d.get(size=self.p.period)) for d in self.datas)
        x = smapi.add_constant(x, prepend=True)
        x.columns = ("const", "x")
        r_beta = smapi.OLS(y, x).fit()
        self.lines.beta[0] = r_beta.params["x"]


class CointN(PeriodN):
    """Calculates the score (coint_t) and pvalue for a given ``period`` for the
    data feeds

    Uses ``pandas`` and ``statsmodels`` (for ``coint``)


    """

    _mindatas = 2  # ensure at least 2 data feeds are passed

    packages = (("pandas", "pd"),)  # import pandas as pd
    # from st... import coint
    frompackages = (("statsmodels.tsa.stattools", "coint"),)

    lines = (
        "score",
        "pvalue",
    )
    params = (
        ("period", 10),
        ("trend", "c"),  # see statsmodel.tsa.statttools
    )

    def next(self):
        """ """
        x, y = (pd.Series(d.get(size=self.p.period)) for d in self.datas)
        score, pvalue, _ = coint(x, y, trend=self.p.trend)
        self.lines.score[0] = score
        self.lines.pvalue[0] = pvalue
