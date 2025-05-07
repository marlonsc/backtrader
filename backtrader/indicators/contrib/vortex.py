"""Vortex Indicator module.

This module implements the Vortex Indicator (VI), which is designed to identify
the start of a new trend or a continuation of an existing trend. It consists of
two oscillators that capture positive and negative trend movement."""

# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2024 Daniel Rodriguez
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

from ...indicator import Indicator
from ..basicops import Max, SumN

__all__ = ["Vortex"]


class Vortex(Indicator):
"""Vortex Indicator implementation.
    
    The Vortex Indicator (VI) is designed to identify the start of a new trend or 
    a continuation of an existing trend. It consists of two oscillators that capture 
    positive and negative trend movement.
    
    Formula:
    - VM+ = Sum of |Current High - Prior Low| for the specified period
    - VM- = Sum of |Current Low - Prior High| for the specified period
    - TR = Sum of True Range for the specified period
    - VI+ = VM+ / TR
    - VI- = VM- / TR
    
    Interpretation:
    - When VI+ crosses above VI-, it may indicate the start of an uptrend
    - When VI- crosses above VI+, it may indicate the start of a downtrend
    
    See:
        - http://www.vortexindicator.com/VFX_VORTEX.PDF"""
    """

    lines = (
        "vi_plus",
        "vi_minus",
    )

    params = (("period", 14),)

    plotlines = dict(vi_plus=dict(_name="+VI"), vi_minus=dict(_name="-VI"))

    def __init__(self):
"""Initialize the Vortex indicator.
        
        Calculates the VI+ and VI- lines based on the formula."""
        """
        h0l1 = abs(self.data.high(0) - self.data.low(-1))
        vm_plus = SumN(h0l1, period=self.p.period)

        l0h1 = abs(self.data.low(0) - self.data.high(-1))
        vm_minus = SumN(l0h1, period=self.p.period)

        h0c1 = abs(self.data.high(0) - self.data.close(-1))
        l0c1 = abs(self.data.low(0) - self.data.close(-1))
        h0l0 = abs(self.data.high(0) - self.data.low(0))

        tr = SumN(Max(h0l0, h0c1, l0c1), period=self.p.period)

        self.l.vi_plus = vm_plus / tr
        self.l.vi_minus = vm_minus / tr
