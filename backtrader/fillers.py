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

from .metabase import MetaParams
from .utils.py3 import MAXINT, with_metaclass


class FixedSize(with_metaclass(MetaParams, object)):
    """
    Returns the volume in a bar. The maximum size is set with the parameter 'size'.
    All docstrings and comments must be line-wrapped at 90 characters or less.
    """

    params = (("size", None),)

    def __call__(self, order, price, ago):
        """

        :param order:
        :param price:
        :param ago:

        """
        p = getattr(self, "p", None)
        size = getattr(p, "size", None)
        if size is None and hasattr(self, "params"):
            size = self.params[0][1]
        size = size or MAXINT
        return min((order.data.volume[ago], abs(order.executed.remsize), size))


class FixedBarPerc(with_metaclass(MetaParams, object)):
    """
    Returns the volume in a bar as a percentage set with the parameter 'perc'.
    All docstrings and comments must be line-wrapped at 90 characters or less.
    """

    params = (("perc", 100.0),)

    def __call__(self, order, price, ago):
        """

        :param order:
        :param price:
        :param ago:

        """
        p = getattr(self, "p", None)
        perc = getattr(p, "perc", None)
        if perc is None and hasattr(self, "params"):
            perc = self.params[0][1]
        perc = perc if perc is not None else 100.0
        maxsize = (order.data.volume[ago] * perc) // 100
        # Return the maximum possible executed volume
        return min(maxsize, abs(order.executed.remsize))


class BarPointPerc(with_metaclass(MetaParams, object)):
    """
    Returns the volume distributed uniformly in the range high-low using 'minmov' to
    partition. The 'perc' percentage will be used from the allocated volume for the
    given price. All docstrings and comments must be line-wrapped at 90 characters or
    less.
    """

    params = (
        ("minmov", None),
        ("perc", 100.0),
    )

    def __call__(self, order, price, ago):
        """

        :param order:
        :param price:
        :param ago:

        """
        data = order.data
        p = getattr(self, "p", None)
        minmov = getattr(p, "minmov", None)
        if minmov is None and hasattr(self, "params"):
            minmov = self.params[0][1]
        parts = 1
        if minmov:
            # high - low + minmov to account for open ended minus op
            parts = (data.high[ago] - data.low[ago] + minmov) // minmov
        perc = getattr(p, "perc", None)
        if perc is None and hasattr(self, "params"):
            perc = self.params[1][1]
        perc = perc if perc is not None else 100.0
        alloc_vol = ((data.volume[ago] / parts) * perc) // 100.0

        # return max possible executable volume
        return min(alloc_vol, abs(order.executed.remsize))
