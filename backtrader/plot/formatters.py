"""formatters.py module.

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

import matplotlib.dates as mdates
import matplotlib.ticker as mplticker

from ..utils import num2date


class MyVolFormatter(mplticker.Formatter):
""""""
"""Args::
    volmax:"""
"""Args::
    y: 
    pos: (Default value = 0)"""
    pos: (Default value = 0)"""

        if y > self.volmax * 1.20:
            return ""

        y = int(y / self.divisor)
        return "%d%s" % (y, self.suffix)


class MyDateFormatter(mplticker.Formatter):
""""""
"""Args::
    dates: 
    fmt: (Default value = "%Y-%m-%d")"""
    fmt: (Default value = "%Y-%m-%d")"""
        self.dates = dates
        self.lendates = len(dates)
        self.fmt = fmt

    def __call__(self, x, pos=0):
"""Args::
    x: 
    pos: (Default value = 0)"""
    pos: (Default value = 0)"""
        ind = int(round(x))
        if ind >= self.lendates:
            ind = self.lendates - 1

        if ind < 0:
            ind = 0

        return num2date(self.dates[ind]).strftime(self.fmt)


def patch_locator(locator, xdates):
"""Args::
    locator: 
    xdates:"""
    xdates:"""

    def _patched_datalim_to_dt(self):
""""""
""""""
"""Args::
    formatter: 
    xdates:"""
    xdates:"""

    def newcall(self, x, pos=0):
"""Args::
    x: 
    pos: (Default value = 0)"""
    pos: (Default value = 0)"""
        if False and x < 0:
            raise ValueError(
                "DateFormatter found a value of x=0, which is "
                "an illegal date.  This usually occurs because "
                "you have not informed the axis that it is "
                "plotting dates, e.g., with ax.xaxis_date()"
            )

        x = xdates[int(x)]
        dt = num2date(x, self.tz)
        return self.strftime(dt, self.fmt)

    bound_call = newcall.__get__(formatter, formatter.__class__)
    formatter.__call__ = bound_call


def getlocator(xdates, numticks=5, tz=None):
"""Args::
    xdates: 
    numticks: (Default value = 5)
    tz: (Default value = None)"""
    tz: (Default value = None)"""
    span = xdates[-1] - xdates[0]

    locator, formatter = mdates.date_ticker_factory(span=span, tz=tz, numticks=numticks)

    patch_locator(locator, xdates)
    patch_formatter(formatter, xdates)
    return locator, formatter
