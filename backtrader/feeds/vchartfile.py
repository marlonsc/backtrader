"""vchartfile.py module.

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

import os.path
from datetime import datetime
from struct import unpack

import backtrader as bt
from backtrader import date2num  # avoid dict lookups


class MetaVChartFile(bt.DataBase.__class__):
""""""
"""Class has already been created ... register

Args::
    name: 
    bases: 
    dct:"""
    dct:"""
        # Initialize the class
        super(MetaVChartFile, cls).__init__(name, bases, dct)

        # Register with the store
        bt.stores.VChartFileStore.DataCls = cls


class VChartFile(bt.with_metaclass(MetaVChartFile, bt.DataBase)):
    """Support for `Visual Chart <www.visualchart.com>`_ binary on-disk files for
both daily and intradaily formats.
Note:
- ``dataname``: Market code displayed by Visual Chart. Example: 015ES for
EuroStoxx 50 continuous future"""

    def start(self):
""""""
""""""
""""""
        if self.f is None:
            return False  # cannot load more

        try:
            bardata = self.f.read(self._barsize)
        except IOError:
            self.f = None  # cannot return, nullify file
            return False  # cannot load more

        if not bardata or len(bardata) < self._barsize:
            self.f = None  # cannot return, nullify file
            return False  # cannot load more

        try:
            bdata = unpack(self._barfmt, bardata)
        except BaseException:
            self.f = None
            return False

        # First Date
        y, md = divmod(bdata[0], 500)  # Years stored as if they had 500 days
        m, d = divmod(md, 32)  # Months stored as if they had 32 days
        dt = datetime(y, m, d)

        # Time
        if self._dtsize > 1:  # Minute Bars
            # Daily Time is stored in seconds
            hhmm, ss = divmod(bdata[1], 60)
            hh, mm = divmod(hhmm, 60)
            dt = dt.replace(hour=hh, minute=mm, second=ss)
        else:  # Daily Bars
            dt = datetime.combine(dt, self.p.sessionend)

        self.lines.datetime[0] = date2num(dt)  # Store time

        # Get the rest of the fields
        o, h, l, c, v, oi = bdata[self._dtsize :]
        self.lines.open[0] = o
        self.lines.high[0] = h
        self.lines.low[0] = l
        self.lines.close[0] = c
        self.lines.volume[0] = v
        self.lines.openinterest[0] = oi

        return True  # a bar has been successfully loaded
