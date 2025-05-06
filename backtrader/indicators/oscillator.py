"""oscillator.py module.

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

import sys

from . import Indicator, MovingAverage


class OscillatorMixIn(Indicator):
    """MixIn class to create a subclass with another indicator. The main line of
that indicator will be substracted from the other base class main line
creating an oscillator
The usage is:
- Class XXXOscillator(XXX, OscillatorMixIn)
Formula:
- XXX calculates lines[0]
- osc = self.data - XXX.lines[0]"""

    plotlines = dict(_0=dict(_name="osc"))

    def _plotinit(self):
""""""
""""""
    """Oscillation of a given data around another data
Datas:
This indicator can accept 1 or 2 datas for the calculation.
- If 1 data is provided, it must be a complex "Lines" object (indicator)
which also has "datas". Example: A moving average
The calculated oscillation will be that of the Moving Average (in the
example) around the data that was used for the average calculation
- If 2 datas are provided the calculated oscillation will be that of the
2nd data around the 1st data
Formula:
- 1 data -> osc = data.data - data
- 2 datas -> osc = data0 - data1"""

    lines = ("osc",)

    # Have a default value which can be later modified if needed
    plotlines = dict(_0=dict(_name="osc"))

    def _plotinit(self):
""""""
""""""
    _newclsdoc = """
    Oscillation of a %s around its data
    """
    # Skip aliases - they will be created automatically
    if getattr(movav, "aliased", ""):
        continue

    movname = movav.__name__
    linename = movav.lines._getlinealias(0)
    newclsname = movname + "Oscillator"

    newaliases = [movname + "Osc"]
    for alias in getattr(movav, "alias", []):
        for suffix in ["Oscillator", "Osc"]:
            newaliases.append(alias + suffix)

    newclsdoc = _newclsdoc % movname
    newclsdct = {
        "__doc__": newclsdoc,
        "__module__": OscillatorMixIn.__module__,
        "_notregister": True,
        "alias": newaliases,
    }

    newcls = type(str(newclsname), (movav, OscillatorMixIn), newclsdct)
    module = sys.modules[OscillatorMixIn.__module__]
    setattr(module, newclsname, newcls)
