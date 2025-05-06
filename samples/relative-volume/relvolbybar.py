"""RelativeVolumeByBar: Backtrader indicator for relative volume by bar session time.
Implements a session-aware volume ratio for each bar in a trading day.
Copyright (C) 2015-2024 Daniel Rodriguez
This program is free software: you can redistribute it and/or modify it under the terms
of the GNU General Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.
If not, see <http://www.gnu.org/licenses/>."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import collections
import datetime

import backtrader as bt


class RelativeVolumeByBar(bt.Indicator):
    """RelativeVolumeByBar: Backtrader indicator for relative volume by bar session time.
    Implements a session-aware volume ratio for each bar in a trading day.
    by <marlonsc@gmail.com>


    """

    alias = ("RVBB",)
    lines = ("rvbb",)

    params = (
        ("prestart", datetime.time(8, 0)),
        ("start", datetime.time(9, 10)),
        ("end", datetime.time(17, 15)),
    )

    def _plotlabel(self):
        """ """
        plabels = [
            f"prestart: {self.p.prestart.strftime('%H:%M')}",
            f"start: {self.p.start.strftime('%H:%M')}",
            f"end: {self.p.end.strftime('%H:%M')}",
        ]
        return plabels

    def __init__(self):
        """Initialize indicator and internal state."""
        minbuffer = self._calcbuffer()
        self.addminperiod(minbuffer)
        self.pvol = dict()
        self.vcount = collections.defaultdict(int)
        self.days = 0
        self.dtlast = datetime.date.min
        super(RelativeVolumeByBar, self).__init__()

    def _barisvalid(self, tm):
        """Check if the bar time is within the valid session window.

Args:
    tm:"""
        return self.p.start <= tm <= self.p.end

    def _daycount(self):
        """Update the day counter if a new day is detected."""
        dt = self.data.datetime.date()
        if dt > self.dtlast:
            self.days += 1
            self.dtlast = dt

    def prenext(self):
        """Handle logic for bars before minimum period is reached."""
        self._daycount()
        tm = self.data.datetime.time()
        if self._barisvalid(tm):
            self.pvol[tm] = self.data.volume[0]
            self.vcount[tm] += 1

    def next(self):
        """Main logic for each new bar."""
        self._daycount()
        tm = self.data.datetime.time()
        if not self._barisvalid(tm):
            return
        self.vcount[tm] += 1
        vol = self.data.volume[0]
        if self.vcount[tm] == self.days and self.pvol.get(tm, 0) != 0:
            getattr(self.lines, "rvbb")[0] = vol / self.pvol[tm]
        self.vcount[tm] = self.days
        self.pvol[tm] = vol

    def _calcbuffer(self):
        """Calculate the minimum buffer period for the indicator."""
        minend = self.p.end.hour * 60 + self.p.end.minute
        minstart = self.p.prestart.hour * 60 + self.p.prestart.minute
        minbuffer = minend - minstart
        tframe = getattr(self.data, "_timeframe", bt.TimeFrame.Minutes)
        tcomp = getattr(self.data, "_compression", 1)
        # Use 1 as a fallback for minperiod if not defined
        minperiod = 1
        if tframe == bt.TimeFrame.Seconds:
            minbuffer = minperiod * 60
        minbuffer = (minbuffer // tcomp) + tcomp
        return minbuffer
