"""vchart.py module.

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

import datetime
import os.path
import struct

from .. import TimeFrame, feed
from ..utils import date2num


class VChartData(feed.DataBase):
    """Support for `Visual Chart <www.visualchart.com>`_ binary on-disk files for
both daily and intradaily formats.
Note:
- ``dataname``: to file or open file-like object
If a file-like object is passed, the ``timeframe`` parameter will be
used to determine which is the actual timeframe.
Else the file extension (``.fd`` for daily and ``.min`` for intraday)
will be used."""

    def start(self):
""""""
""""""
""""""
""""""
"""Args::
    dataname:"""
    dataname:"""
        maincode = dataname[0:2]
        subcode = dataname[2:6]

        datapath = os.path.join(
            self.p.basepath,
            "RealServer",
            "Data",
            maincode,
            subcode,  # 01 00XX
            dataname,
        )

        newkwargs = self.p._getkwargs()
        newkwargs.update(kwargs)
        kwargs["dataname"] = datapath
        return self.DataCls(**kwargs)
