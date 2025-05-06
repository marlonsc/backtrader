"""psar.py module.

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

from . import PeriodN

__all__ = ["ParabolicSAR", "PSAR"]


class _SarStatus(object):
""""""
""""""
    """Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
Technical Trading Systems"* for the RSI
SAR stands for *Stop and Reverse* and the indicator was meant as a signal
for entry (and reverse)
How to select the 1st signal is left unspecified in the book and the
increase/decrease of bars
See:
- https://en.wikipedia.org/wiki/Parabolic_SAR
- http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:parabolic_sar"""

    alias = ("PSAR",)
    lines = ("psar",)
    params = (
        ("period", 2),  # when to start showing values
        ("af", 0.02),
        ("afmax", 0.20),
    )

    plotinfo = dict(subplot=False)
    plotlines = dict(
        psar=dict(marker=".", markersize=4.0, color="black", fillstyle="full", ls=""),
    )

    def prenext(self):
""""""
""""""
""""""
        hi = self.data.high[0]
        lo = self.data.low[0]

        plenidx = (len(self) - 1) % 2  # previous length index (0 or 1)
        status = self._status[plenidx]  # use prev status for calculations

        tr = status.tr
        sar = status.sar

        # Check if the sar penetrated the price to switch the trend
        if (tr and sar >= lo) or (not tr and sar <= hi):
            tr = not tr  # reverse the trend
            sar = status.ep  # new sar is prev SIP (Significant price)
            ep = hi if tr else lo  # select new SIP / Extreme Price
            af = self.p.af  # reset acceleration factor

        else:  # use the precalculated values
            ep = status.ep
            af = status.af

        # Update sar value for today
        self.lines.psar[0] = sar

        # Update ep and af if needed
        if tr:  # long trade
            if hi > ep:
                ep = hi
                af = min(af + self.p.af, self.p.afmax)

        else:  # downtrend
            if lo < ep:
                ep = lo
                af = min(af + self.p.af, self.p.afmax)

        sar = sar + af * (ep - sar)  # calculate the sar for tomorrow

        # make sure sar doesn't go into hi/lows
        if tr:  # long trade
            lo1 = self.data.low[-1]
            if sar > lo or sar > lo1:
                sar = min(lo, lo1)  # sar not above last 2 lows -> lower
        else:
            hi1 = self.data.high[-1]
            if sar < hi or sar < hi1:
                sar = max(hi, hi1)  # sar not below last 2 highs -> highest

        # new status has been calculated, keep it in current length
        # will be used when length moves forward
        newstatus = self._status[not plenidx]
        newstatus.tr = tr
        newstatus.sar = sar
        newstatus.ep = ep
        newstatus.af = af
