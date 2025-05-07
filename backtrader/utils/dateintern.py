"""dateintern.py module.

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

import datetime
import math
import time as _time

from .py3 import string_types

ZERO = datetime.timedelta(0)

STDOFFSET = datetime.timedelta(seconds=-_time.timezone)
if _time.daylight:
    DSTOFFSET = datetime.timedelta(seconds=-_time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

# To avoid rounding errors taking dates to next day
TIME_MAX = datetime.time(23, 59, 59, 999990)

# To avoid rounding errors taking dates to next day
TIME_MIN = datetime.time.min


def tzparse(tz):
"""Args::
    tz:"""
"""Args::
    tz:"""
"""Args::
    dt:"""
    """UTC"""

    def utcoffset(self, dt):
"""Args::
    dt:"""
"""Args::
    dt:"""
"""Args::
    dt:"""
"""Args::
    dt:"""
""""""
"""Args::
    dt:"""
"""Args::
    dt:"""
"""Args::
    dt:"""
"""Args::
    dt:"""
"""Args::
    dt:"""
"""Args::
    x: 
    tz: (Default value = None)
    naive: (Default value = True)"""
    naive: (Default value = True)"""
    # Same as matplotlib except if tz is None a naive datetime object
    # will be returned.
    """
    *x* is a float value which gives the number of days
    (fraction part represents hours, minutes, seconds) since
    0001-01-01 00:00:00 UTC *plus* *one*.
    The addition of one here is a historical artifact.  Also, note
    that the Gregorian calendar is assumed; this is not universal
    practice.  For details, see the module docstring.
    Return value is a :class:`datetime` instance in timezone *tz* (default to
    rcparams TZ value).
    If *x* is a sequence, a sequence of :class:`datetime` objects will
    be returned.
    """

    ix = int(x)
    dt = datetime.datetime.fromordinal(ix)
    remainder = float(x) - ix
    hour, remainder = divmod(HOURS_PER_DAY * remainder, 1)
    minute, remainder = divmod(MINUTES_PER_HOUR * remainder, 1)
    second, remainder = divmod(SECONDS_PER_MINUTE * remainder, 1)
    microsecond = int(MUSECONDS_PER_SECOND * remainder)
    if microsecond < 10:
        microsecond = 0  # compensate for rounding errors

    if True and tz is not None:
        dt = datetime.datetime(
            dt.year,
            dt.month,
            dt.day,
            int(hour),
            int(minute),
            int(second),
            microsecond,
            tzinfo=UTC,
        )
        dt = dt.astimezone(tz)
        if naive:
            dt = dt.replace(tzinfo=None)
    else:
        # If not tz has been passed return a non-timezoned dt
        dt = datetime.datetime(
            dt.year,
            dt.month,
            dt.day,
            int(hour),
            int(minute),
            int(second),
            microsecond,
        )

    if microsecond > 999990:  # compensate for rounding errors
        dt += datetime.timedelta(microseconds=1e6 - microsecond)

    return dt


def num2dt(num, tz=None, naive=True):
"""Args::
    num: 
    tz: (Default value = None)
    naive: (Default value = True)"""
    naive: (Default value = True)"""
    return num2date(num, tz=tz, naive=naive).date()


def num2time(num, tz=None, naive=True):
"""Args::
    num: 
    tz: (Default value = None)
    naive: (Default value = True)"""
    naive: (Default value = True)"""
    return num2date(num, tz=tz, naive=naive).time()


def date2num(dt, tz=None):
"""Convert :mod:`datetime` to the Gregorian date as UTC float days,
preserving hours, minutes, seconds and microseconds.  Return value
is a :func:`float`.

Args::
    dt: 
    tz: (Default value = None)"""
    tz: (Default value = None)"""
    if tz is not None:
        dt = tz.localize(dt)

    if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
        delta = dt.tzinfo.utcoffset(dt)
        if delta is not None:
            dt -= delta

    base = float(dt.toordinal())
    if hasattr(dt, "hour"):
        # base += (dt.hour / HOURS_PER_DAY +
        #          dt.minute / MINUTES_PER_DAY +
        #          dt.second / SECONDS_PER_DAY +
        #          dt.microsecond / MUSECONDS_PER_DAY
        #         )
        base = math.fsum(
            (
                base,
                dt.hour / HOURS_PER_DAY,
                dt.minute / MINUTES_PER_DAY,
                dt.second / SECONDS_PER_DAY,
                dt.microsecond / MUSECONDS_PER_DAY,
            )
        )

    return base


def time2num(tm):
"""Converts the hour/minute/second/microsecond part of tm (datetime.datetime
or time) to a num

Args::
    tm:"""
    tm:"""
    num = (
        tm.hour / HOURS_PER_DAY
        + tm.minute / MINUTES_PER_DAY
        + tm.second / SECONDS_PER_DAY
        + tm.microsecond / MUSECONDS_PER_DAY
    )

    return num
