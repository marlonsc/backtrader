"""aroon.py module.

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

from . import FindFirstIndexHighest, FindFirstIndexLowest, Indicator


class _AroonBase(Indicator):
    """Base class which does the calculation of the AroonUp/AroonDown values and
defines the common parameters.
It uses the class attributes _up and _down (boolean flags) to decide which
value has to be calculated.
Values are not assigned to lines but rather stored in the "up" and "down"
instance variables, which can be used by subclasses to for assignment or
further calculations"""

    _up = False
    _down = False

    params = (
        ("period", 14),
        ("upperband", 70),
        ("lowerband", 30),
    )
    plotinfo = dict(plotymargin=0.05, plotyhlines=[0, 100])

    def _plotlabel(self):
""""""
""""""
""""""
    """This is the AroonUp from the indicator AroonUpDown developed by Tushar
Chande in 1995.
Formula:
- up = 100 * (period - distance to highest high) / period
Note:
The lines oscillate between 0 and 100. That means that the "distance" to
the last highest or lowest must go from 0 to period so that the formula
can yield 0 and 100.
Hence the lookback period is period + 1, because the current bar is also
taken into account. And therefore this indicator needs an effective
lookback period of period + 1.
See:
- http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:aroon"""

    _up = True

    lines = ("aroonup",)

    def __init__(self):
""""""
    """This is the AroonDown from the indicator AroonUpDown developed by Tushar
Chande in 1995.
Formula:
- down = 100 * (period - distance to lowest low) / period
Note:
The lines oscillate between 0 and 100. That means that the "distance" to
the last highest or lowest must go from 0 to period so that the formula
can yield 0 and 100.
Hence the lookback period is period + 1, because the current bar is also
taken into account. And therefore this indicator needs an effective
lookback period of period + 1.
See:
- http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:aroon"""

    _down = True

    lines = ("aroondown",)

    def __init__(self):
""""""
    """Developed by Tushar Chande in 1995.
It tries to determine if a trend exists or not by calculating how far away
within a given period the last highs/lows are (AroonUp/AroonDown)
Formula:
- up = 100 * (period - distance to highest high) / period
- down = 100 * (period - distance to lowest low) / period
Note:
The lines oscillate between 0 and 100. That means that the "distance" to
the last highest or lowest must go from 0 to period so that the formula
can yield 0 and 100.
Hence the lookback period is period + 1, because the current bar is also
taken into account. And therefore this indicator needs an effective
lookback period of period + 1.
See:
- http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:aroon"""

    alias = ("AroonIndicator",)


class AroonOscillator(_AroonBase):
    """It is a variation of the AroonUpDown indicator which shows the current
difference between the AroonUp and AroonDown value, trying to present a
visualization which indicates which is stronger (greater than 0 -> AroonUp
and less than 0 -> AroonDown)
Formula:
- aroonosc = aroonup - aroondown
See:
- http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:aroon"""

    _up = True
    _down = True

    alias = ("AroonOsc",)

    lines = ("aroonosc",)

    def _plotinit(self):
""""""
""""""
    """Presents together the indicators AroonUpDown and AroonOsc
Formula:
(None, uses the aforementioned indicators)
See:
- http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:aroon"""

    alias = ("AroonUpDownOsc",)
