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

try:
    pass
except ImportError:
    pass  # The user may not have ibpy installed

try:
    pass
except ImportError:
    pass  # The user may not have something installed

try:
    pass
except ImportError:
    pass  # The user may not have something installed

from .btcsv import BacktraderCSVData
from .csvgeneric import GenericCSVData
from .ibdata import IBData
from .mt4csv import MT4CSVData
from .oanda import OandaData
from .pandafeed import PandasData
from .sierrachart import SierraChartCSVData
from .vcdata import VCData
from .vchartcsv import VChartCSVData
from .vchartfile import VChartFile
from .yahoo import YahooFinanceCSVData, YahooFinanceData

__all__ = [
    "BacktraderCSVData",
    "VChartCSVData",
    "VChartFile",
    "SierraChartCSVData",
    "MT4CSVData",
    "YahooFinanceCSVData",
    "YahooFinanceData",
    "VCData",
    "IBData",
    "OandaData",
    "PandasData",
    "GenericCSVData",
]
