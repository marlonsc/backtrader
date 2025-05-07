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

from datetime import datetime, time, timedelta

from .metabase import MetaParams
from .utils import UTC
from .utils.py3 import string_types, with_metaclass

__all__ = ["TradingCalendarBase", "TradingCalendar", "PandasMarketCalendar"]

# Imprecission in the full time conversion to float would wrap over to next day
# if microseconds is 999999 as defined in time.max
_time_max = time(hour=23, minute=59, second=59, microsecond=999990)

MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)
(
    ISONODAY,
    ISOMONDAY,
    ISOTUESDAY,
    ISOWEDNESDAY,
    ISOTHURSDAY,
    ISOFRIDAY,
    ISOSATURDAY,
    ISOSUNDAY,
) = range(8)

WEEKEND = [SATURDAY, SUNDAY]
ISOWEEKEND = [ISOSATURDAY, ISOSUNDAY]
ONEDAY = timedelta(days=1)


class TradingCalendarBase(with_metaclass(MetaParams, object)):
    """ """

    def _nextday(self, day):
        """Returns the next trading day (datetime/date instance) after ``day``
(datetime/date instance) and the isocalendar components
The return value is a tuple with 2 components: (nextday, (y, w, d))

Args:
    day:"""
        raise NotImplementedError

    def schedule(self, day):
        """Returns a tuple with the opening and closing times (``datetime.time``)
for the given ``date`` (``datetime/date`` instance)

Args:
    day:"""
        raise NotImplementedError

    def nextday(self, day):
        """Returns the next trading day (datetime/date instance) after ``day``
(datetime/date instance)

Args:
    day:"""
        return self._nextday(day)[0]  # 1st ret elem is next day

    def nextday_week(self, day):
        """Returns the iso week number of the next trading day, given a ``day``
(datetime/date) instance

Args:
    day:"""
        self._nextday(day)[1][1]  # 2 elem is isocal / 0 - y, 1 - wk, 2 - day

    def last_weekday(self, day):
        """Returns ``True`` if the given ``day`` (datetime/date) instance is the
last trading day of this week

Args:
    day:"""
        # Next day must be greater than day. If the week changes is enough for
        # a week change even if the number is smaller (year change)
        return day.isocalendar()[1] != self._nextday(day)[1][1]

    def last_monthday(self, day):
        """Returns ``True`` if the given ``day`` (datetime/date) instance is the
last trading day of this month

Args:
    day:"""
        # Next day must be greater than day. If the week changes is enough for
        # a week change even if the number is smaller (year change)
        return day.month != self._nextday(day)[0].month

    def last_yearday(self, day):
        """Returns ``True`` if the given ``day`` (datetime/date) instance is the
last trading day of this month

Args:
    day:"""
        # Next day must be greater than day. If the week changes is enough for
        # a week change even if the number is smaller (year change)
        return day.year != self._nextday(day)[0].year


class TradingCalendar(TradingCalendarBase):
    """Wrapper of ``pandas_market_calendars`` for a trading calendar. The package
    ``pandas_market_calendar`` must be installed


    """

    params = (
        ("open", time.min),
        ("close", _time_max),
        ("holidays", []),  # list of non trading days (date)
        ("earlydays", []),  # list of tuples (date, opentime, closetime)
        ("offdays", ISOWEEKEND),  # list of non trading (isoweekdays)
    )

    def __init__(self):
        """ """
        self._earlydays = [x[0] for x in self.p.earlydays]  # speed up searches

    def _nextday(self, day):
        """Returns the next trading day (datetime/date instance) after ``day``
(datetime/date instance) and the isocalendar components
The return value is a tuple with 2 components: (nextday, (y, w, d))

Args:
    day:"""
        while True:
            day += ONEDAY
            isocal = day.isocalendar()
            if isocal[2] in self.p.offdays or day in self.p.holidays:
                continue

            return day, isocal

    def schedule(self, ts, tz=None):
        """Returns the opening and closing times for the given ``day``. If the
method is called, the assumption is that ``day`` is an actual trading
day
The return value is a tuple with 2 components: opentime, closetime
Input datetime is either a naive datetime object or a aware datetime.

Args:
    ts: 
    tz: (Default value = None)

Returns:
    ts is meant to be an aware datetime while tz is the timezone of opening/closing times."""
        if ts.tzinfo is not None:
            raise RuntimeError(
                "Parameter ts is an aware datetime object but is expected to be naive!"
            )

        def tzshift(dt):
            """Args:
    dt:"""
            if tz is None:
                return dt
            return tz.localize(dt).astimezone(UTC).replace(tzinfo=None)

        ts = tzshift(ts)

        # go back 1 extra day to account for possible timezone drift
        searchdate = (ts - 2 * ONEDAY).date()
        while True:
            searchdate = self._nextday(searchdate)[0]
            try:
                i = self._earlydays.index(searchdate)
                o, c = self.p.earlydays[i][1:]
            except ValueError:  # not found
                o, c = self.p.open, self.p.close

            closing = datetime.combine(searchdate, c)
            closing = tzshift(closing)

            if ts >= closing:  # current time over eos
                continue

            opening = datetime.combine(searchdate, o)
            opening = tzshift(opening)

            return opening, closing


class PandasMarketCalendar(TradingCalendarBase):
    """Wrapper of ``pandas_market_calendars`` for a trading calendar. The package
    ``pandas_market_calendar`` must be installed


    """

    params = (
        ("calendar", None),  # A pandas_market_calendars instance or exch name
        ("cachesize", 365),  # Number of days to cache in advance
    )

    def __init__(self):
        """ """
        self._calendar = self.p.calendar

        if isinstance(self._calendar, string_types):  # use passed mkt name
            try:
                import pandas_market_calendars as mcal
            except ImportError:
                raise ImportError(
                    "pandas_market_calendars is required for PandasMarketCalendar. "
                    "Please install it via pip."
                )
            self._calendar = mcal.get_calendar(self._calendar)

        import pandas as pd  # guaranteed because of pandas_market_calendars

        self.dcache = pd.DatetimeIndex([0.0])
        self.idcache = pd.DataFrame(index=pd.DatetimeIndex([0.0]))
        self.csize = timedelta(days=self.p.cachesize)

    def _nextday(self, day):
        """Returns the next trading day (datetime/date instance) after ``day``
(datetime/date instance) and the isocalendar components
The return value is a tuple with 2 components: (nextday, (y, w, d))

Args:
    day:"""
        day += ONEDAY
        while True:
            i = self.dcache.searchsorted(day)
            if i == len(self.dcache):
                # keep a cache of 1 year to speed up searching
                self.dcache = self._calendar.valid_days(day, day + self.csize)
                continue

            d = self.dcache[i].to_pydatetime()
            return d, d.isocalendar()

    def schedule(self, day, tz=None):
        """Returns the opening and closing times for the given ``day``. If the
method is called, the assumption is that ``day`` is an actual trading
day
The return value is a tuple with 2 components: opentime, closetime

Args:
    day: 
    tz: (Default value = None)"""
        while True:
            i = self.idcache.index.searchsorted(day.date())
            if i == len(self.idcache):
                # keep a cache of 1 year to speed up searching
                self.idcache = self._calendar.schedule(day, day + self.csize)
                continue

            st = (x.tz_localize(None) for x in self.idcache.iloc[i, 0:2])
            opening, closing = st  # Get utc naive times
            if day > closing:  # passed time is over the sessionend
                day += ONEDAY  # wrap over to next day
                continue

            return opening.to_pydatetime(), closing.to_pydatetime()
