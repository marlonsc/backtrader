"""talib.py module.

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

from .cerebro import Cerebro
from .indicator import Indicator
from .metabase import findowner
from .utils.py3 import with_metaclass

# The modules below should/must define __all__ with the objects wishes
# or prepend an "_" (underscore) to private classes/variables

try:
    import talib
except ImportError:
    __all__ = []  # talib is not available
else:
    import numpy as np  # talib dependency
    import talib.abstract

    MA_Type = talib.MA_Type

    # Reverse TA_FUNC_FLAGS dict
    R_TA_FUNC_FLAGS = dict(
        zip(
            talib.abstract.TA_FUNC_FLAGS.values(),
            talib.abstract.TA_FUNC_FLAGS.keys(),
        )
    )

    FUNC_FLAGS_SAMESCALE = 16777216
    FUNC_FLAGS_UNSTABLE = 134217728
    FUNC_FLAGS_CANDLESTICK = 268435456

    R_TA_OUTPUT_FLAGS = dict(
        zip(
            talib.abstract.TA_OUTPUT_FLAGS.values(),
            talib.abstract.TA_OUTPUT_FLAGS.keys(),
        )
    )

    OUT_FLAGS_LINE = 1
    OUT_FLAGS_DOTTED = 2
    OUT_FLAGS_DASH = 4
    OUT_FLAGS_HISTO = 16
    OUT_FLAGS_UPPER = 2048
    OUT_FLAGS_LOWER = 4096

    # Generate all indicators as subclasses

    class _MetaTALibIndicator(Indicator.__class__):
""""""
"""Args::
    _obj:"""
""""""
"""Args::
    name:"""
"""Args::
    start: 
    end:"""
    end:"""
            pass  # if not ... a call with a single value to once will happen

        def once(self, start, end):
"""Args::
    start: 
    end:"""
    end:"""
            import array

            # prepare the data arrays - single shot
            narrays = [np.array(x.lines[0].array) for x in self.datas]
            # Execute
            output = self._tafunc(*narrays, **self.p._getkwargs())

            fsize = self.size()
            lsize = fsize - self._iscandle
            if lsize == 1:  # only 1 output, no tuple returned
                self.lines[0].array = array.array(str("d"), output)

                if fsize > lsize:  # candle is present
                    candleref = narrays[self.CANDLEREF] * self.CANDLEOVER
                    output2 = candleref * (output / 100.0)
                    self.lines[1].array = array.array(str("d"), output2)

            else:
                for i, o in enumerate(output):
                    self.lines[i].array = array.array(str("d"), o)

        def next(self):
""""""
            # prepare the data arrays - single shot
            size = self._lookback or len(self)
            narrays = [np.array(x.lines[0].get(size=size)) for x in self.datas]

            out = self._tafunc(*narrays, **self.p._getkwargs())

            fsize = self.size()
            lsize = fsize - self._iscandle
            if lsize == 1:  # only 1 output, no tuple returned
                self.lines[0][0] = o = out[-1]

                if fsize > lsize:  # candle is present
                    candleref = narrays[self.CANDLEREF][-1] * self.CANDLEOVER
                    o2 = candleref * (o / 100.0)
                    self.lines[1][0] = o2

            else:
                for i, o in enumerate(out):
                    self.lines[i][0] = o[-1]

    # When importing the module do an automatic declaration of thed
    tafunctions = talib.get_functions()
    for tafunc in tafunctions:
        _TALibIndicator._subclass(tafunc)

    __all__ = tafunctions + ["MA_Type", "_TALibIndicator"]
