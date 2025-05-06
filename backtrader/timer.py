"""timer.py module.

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

import bisect
import collections
from datetime import date, datetime, timedelta

from .feed import AbstractDataBase
from .metabase import MetaParams
from .utils.date import date2num, num2date

try:
    from .utils.time import TIME_MAX
except ImportError:
    # Fallback if TIME_MAX is not available
    from datetime import time

    TIME_MAX = time(23, 59, 59, 999999)
from .utils.py3 import integer_types, range, with_metaclass

__all__ = ["SESSION_TIME", "SESSION_START", "SESSION_END", "Timer"]

SESSION_TIME, SESSION_START, SESSION_END = range(3)


class Timer(with_metaclass(MetaParams, object)):
""""""
        """"""
        # Ensure self.p is always present
        if not hasattr(self, "p"):

"""DummyParams class.

Description of the class functionality."""
                tid = None
                owner = None
                strats = False
                when = None
                offset = timedelta()
                repeat = timedelta()
                weekdays = []
                weekcarry = False
                monthdays = []
                monthcarry = True
                allow = None
                tzdata = None
                cheat = False

            self.p = DummyParams()
        self.args = args
        self.kwargs = kwargs

    def start(self, data):
"""Args::
    data:"""
"""Args::
    ddate: (Default value = datetime.min)"""
"""Args::
    ddate:"""
"""Args::
    ddate: (Default value = date.min)"""
"""Args::
    dt:"""
    dt:"""
        d = num2date(dt)
        ddate = d.date()
        if self._lastcall == ddate:  # not repeating, awaiting date change
            return False

        if d > self._nexteos:
            if self._isdata:  # eos provided by data
                nexteos, _ = self._tzdata._getnexteos()
            else:  # generic eos
                nexteos = datetime.combine(ddate, TIME_MAX)
            self._nexteos = nexteos
            self._reset_when()

        if ddate > self._curdate:  # day change
            self._curdate = ddate
            ret = self._check_month(ddate)
            if ret:
                ret = self._check_week(ddate)
            if ret and self.p.allow is not None:
                if callable(self.p.allow):
                    ret = self.p.allow(ddate)
                # If not callable, do not change ret

            if not ret:
                self._reset_when(ddate)  # this day won't make it
                return False  # timer target not met

        # no day change or passed month, week and allow filters on date change
        dwhen = self._dwhen
        dtwhen = self._dtwhen
        if dtwhen is None:
            dwhen = datetime.combine(ddate, self._when)
            if self.p.offset:
                dwhen += self.p.offset

            self._dwhen = dwhen

            if self._isdata:
                self._dtwhen = dtwhen = self._tzdata.date2num(dwhen)
            else:
                self._dtwhen = dtwhen = date2num(dwhen, tz=self._tzdata)

        if dt < dtwhen:
            return False  # timer target not met

        self.lastwhen = dwhen  # record when the last timer "when" happened

        if not self.p.repeat:  # cannot repeat
            self._reset_when(ddate)  # reset and mark as called on ddate
        else:
            if d > self._nexteos:
                if self._isdata:  # eos provided by data
                    nexteos, _ = self._tzdata._getnexteos()
                else:  # generic eos
                    nexteos = datetime.combine(ddate, TIME_MAX)

                self._nexteos = nexteos
            else:
                nexteos = self._nexteos

            while True:
                dwhen += self.p.repeat
                if dwhen > nexteos:  # new schedule is beyone session
                    self._reset_when(ddate)  # reset to original point
                    break

                if dwhen > d:  # gone over current datetime
                    self._dtwhen = dtwhen = date2num(dwhen)  # float timestamp
                    # Get the localized expected next time
                    if self._isdata:
                        self._dwhen = self._tzdata.num2date(dtwhen)
                    else:  # assume pytz compatible or None
                        self._dwhen = num2date(dtwhen, tz=self._tzdata)

                    break

        return True  # timer target was met
