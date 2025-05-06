"""drawdown.py module.

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

import backtrader as bt

from .. import Observer


class DrawDown(Observer):
"""This observer keeps track of the current drawdown level (plotted) and
    the maxdrawdown (not plotted) levels"""
    """

    _stclock = True

    params = (("fund", None),)

    lines = (
        "drawdown",
        "maxdrawdown",
    )

    plotinfo = dict(plot=True, subplot=True)

    plotlines = dict(
        maxdrawdown=dict(
            _plotskip=True,
        )
    )

    def __init__(self):
""""""
""""""
"""This observer keeps track of the current drawdown length (plotted) and
    the drawdown max length (not plotted)"""
    """

    _stclock = True

    lines = (
        "len",
        "maxlen",
    )

    plotinfo = dict(plot=True, subplot=True)

    plotlines = dict(
        maxlength=dict(
            _plotskip=True,
        )
    )

    def __init__(self):
""""""
""""""
        self.lines.len[0] = self._dd.rets.len  # update drawdown length
        self.lines.maxlen[0] = self._dd.rets.max.len  # update max length
