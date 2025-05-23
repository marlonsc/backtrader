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

from . import Filter

__all__ = ["Renko"]


class Renko(Filter):
    """Modify the data stream to draw Renko bars (or bricks)"""

    params = (
        ("hilo", False),
        ("size", None),
        ("autosize", 20.0),
        ("dynamic", False),
        ("align", 1.0),
        ("roundstart", True),
    )

    def nextstart(self, data):
        """

        :param data:

        """
        o = data.open[0]
        o = round(o / self.p.align, 0) * self.p.align  # aligned
        self._size = self.p.size or float(o // self.p.autosize)
        if self.p.roundstart:
            o = int(o)

        self._top = o + self._size
        self._bot = o - self._size

    def next(self, data):
        """

        :param data:

        """
        c = data.close[0]
        h = data.high[0]
        l = data.low[0]

        if self.p.hilo:
            hiprice = h
            loprice = l
        else:
            hiprice = loprice = c

        if hiprice >= self._top:
            # deliver a renko brick from top -> top + size
            self._bot = bot = self._top

            if self.p.size is None and self.p.dynamic:
                self._size = float(c // self.p.autosize)
                top = bot + self._size
                top = round(top / self.p.align, 0) * self.p.align  # aligned
            else:
                top = bot + self._size

            self._top = top

            data.open[0] = bot
            data.low[0] = bot
            data.high[0] = top
            data.close[0] = top
            data.volume[0] = 0.0
            data.openinterest[0] = 0.0
            return False  # length of data stream is unaltered

        elif loprice <= self._bot:
            # deliver a renko brick from bot -> bot - size
            self._top = top = self._bot

            if self.p.size is None and self.p.dynamic:
                self._size = float(c // self.p.autosize)
                bot = top - self._size
                bot = round(bot / self.p.align, 0) * self.p.align  # aligned
            else:
                bot = top - self._size

            self._bot = bot

            data.open[0] = top
            data.low[0] = top
            data.high[0] = bot
            data.close[0] = bot
            data.volume[0] = 0.0
            data.openinterest[0] = 0.0
            return False  # length of data stream is unaltered

        data.backwards()
        return True  # length of stream was changed, get new bar
