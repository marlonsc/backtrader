"""broker.py module.

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

from .. import Observer


class Cash(Observer):
    """This observer keeps track of the current amount of cash in the broker"""

    _stclock = True

    lines = ("cash",)

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
""""""
    """This observer keeps track of the current amount of cash in the broker"""

    _stclock = True

    lines = ("mktvalue",)

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
""""""
    """This observer keeps track of the cumulative compounded returns"""

    _stclock = True

    lines = ("cumvalue",)

    plotinfo = dict(plot=True, subplot=True)

    def start(self):
""""""
""""""
"""This observer keeps track of the current portfolio value in the broker
    including the cash"""
    """

    _stclock = True

    params = (("fund", None),)

    lines = ("value",)

    plotinfo = dict(plot=True, subplot=True)

    def start(self):
""""""
""""""
"""This observer keeps track of the current cash amount and portfolio value in
    the broker (including the cash)"""
    """

    _stclock = True

    params = (("fund", None),)

    alias = ("CashValue",)
    lines = ("cash", "value")

    plotinfo = dict(plot=True, subplot=True)

    def start(self):
""""""
""""""
    """This observer keeps track of the current fund-like value"""

    _stclock = True

    alias = ("FundShareValue", "FundVal")
    lines = ("fundval",)

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
""""""
    """This observer keeps track of the current fund-like shares"""

    _stclock = True

    lines = ("fundshares",)

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
""""""
        self.lines.fundshares[0] = self._owner.broker.fundshares
