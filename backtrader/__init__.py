#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (c) 2025 backtrader contributors
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
"""
backtrader package initialization.

Exposes the main public API for the backtrader framework, including core classes
such as Cerebro, Analyzer, Strategy, Observer, Indicator, Signal, and SizerFix.

Attributes:
    feeds: Data feed subpackage.
    TimeFrame: Time frame enumeration.
    Cerebro: Main engine for backtesting and live trading.
    Analyzer: Base class for analyzers.
    Observer: Base class for observers.
    Strategy: Base class for strategies.
    Indicator: Base class for indicators.
    Signal: Base class for signals.
    SizerFix: Fixed size position sizer.
"""
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from .sizers.fixedsize import SizerFix
from . import feeds
from .indicator import Indicator
from .analyzer import Analyzer
from .strategy import Strategy
from .observer import Observer
from .signal import Signal
from .cerebro import Cerebro
from . import TimeFrame

__all__ = [
    "feeds",
    "TimeFrame",
    "Cerebro",
    "Analyzer",
    "Observer",
    "Strategy",
    "Indicator",
    "Signal",
    "SizerFix",
]

# Load contributed indicators and studies
