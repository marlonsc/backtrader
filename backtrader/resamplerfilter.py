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

from datetime import datetime, timedelta

from . import metabase
from .dataseries import TimeFrame, _Bar
from .utils.date import date2num, num2date
from .utils.py3 import with_metaclass


class DTFaker(object):
    """ """

    # This will only be used for data sources which at some point in time
    # return None from _load to indicate that a check of the resampler and/or
    # notification queue is needed
    # This is meant (at least initially) for real-time feeds, because those are
    # the ones in need of events like the ones described above.
    # These data sources should also be producing ``utc`` time directly because
    # the real-time feed is (more often than not)  timestamped and utc provides
    # a universal reference
    # That's why below the timestamp is chosen in UTC and passed directly to
    # date2num to avoid a localization. But it is extracted from data.num2date
    # to ensure the returned datetime object is localized according to the
    # expected output by the user (local timezone or any specified)

    def __init__(self, data, forcedata=None):
        """

        :param data:
        :param forcedata:  (Default value = None)

        """
        self.data = data

        # Aliases
        self.datetime = self
        self.p = self

        if forcedata is None:
            _dtime = datetime.utcnow() + data._timeoffset()
            self._dt = dt = date2num(_dtime)  # utc-like time
            self._dtime = data.num2date(dt)  # localized time
        else:
            self._dt = forcedata.datetime[0]  # utc-like time
            self._dtime = forcedata.datetime.datetime()  # localized time

        self.sessionend = data.p.sessionend

    def __len__(self):
        """ """
        return len(self.data)

    def __call__(self, idx=0):
        """

        :param idx:  (Default value = 0)

        """
        return self._dtime  # simulates data.datetime.datetime()

    def datetime(self, idx=0):
        """

        :param idx:  (Default value = 0)

        """
        return self._dtime

    def date(self, idx=0):
        """

        :param idx:  (Default value = 0)

        """
        return self._dtime.date()

    def time(self, idx=0):
        """

        :param idx:  (Default value = 0)

        """
        return self._dtime.time()

    @property
    def _calendar(self):
        """ """
        return self.data._calendar

    def __getitem__(self, idx):
        """

        :param idx:

        """
        return self._dt if idx == 0 else float("-inf")

    def num2date(self, *args, **kwargs):
        """

        :param *args:
        :param **kwargs:

        """
        return self.data.num2date(*args, **kwargs)

    def date2num(self, *args, **kwargs):
        """

        :param *args:
        :param **kwargs:

        """
        return self.data.date2num(*args, **kwargs)

    def _getnexteos(self):
        """ """
        return self.data._getnexteos()


class _BaseResampler(with_metaclass(metabase.MetaParams, object)):
    """ """

    params = (
        ("bar2edge", True),
        ("adjbartime", True),
        ("rightedge", True),
        ("boundoff", 0),
        ("timeframe", TimeFrame.Days),
        ("compression", 1),
        ("takelate", True),
        ("sessionend", True),
    )

    def __init__(self, data):
        """

        :param data:

        """
        # Downsampling only. Upsampling is not implemented
        assert data._timeframe <= self.p.timeframe
        self.subdays = TimeFrame.Ticks < self.p.timeframe < TimeFrame.Days
        self.subweeks = self.p.timeframe < TimeFrame.Weeks
        self.componly = (
            not self.subdays
            and data._timeframe == self.p.timeframe
            and not (self.p.compression % data._compression)
        )

        # initialize state
        self.bar = None  # bar holder
        self.compcount = None  # count of produced bars to control compression
        self._firstbar = None
        self.reset()

        self.doadjusttime = self.p.bar2edge and self.p.adjbartime and self.subweeks

        self._nexteos = None

        # Modify data information according to own parameters
        data.resampling = 1
        data.replaying = self.replaying
        data._timeframe = data.p.timeframe = self.p.timeframe
        data._compression = data.p.compression = self.p.compression

        self.data = data

    def reset(self):
        """ """
        self.bar = _Bar(maxdate=True)
        self.compcount = 0
        self._firstbar = True
        self._nexteos = None

    def _latedata(self, data):
        """

        :param data:

        """
        # new data at position 0, still untouched from stream
        if not self.subdays:
            return False

        # Time already delivered
        return len(data) > 1 and data.datetime[0] <= data.datetime[-1]

    def _checkbarover(self, data, fromcheck=False, forcedata=None):
        """

        :param data:
        :param fromcheck:  (Default value = False)
        :param forcedata:  (Default value = None)

        """
        chkdata = DTFaker(data, forcedata) if fromcheck else data

        # scenarios:
        # 1 Tick -> 5 Ticks     componly=t subdays=f
        # 2 Ticks -> 5 Ticks    componly=f sbudays=f
        # 1 Tick -> 1 Day       componly=f subdays=f
        # 1 Tick -> 1 Minute    componly=f subdays=t
        # 1 Minute -> 5 Minute  componly=f subdays=t

        # if bar is not over only return False when also timeframe is changed
        # componly also involves checking for odd compressions like 2 -> 5. is this relevant?
        #
        # componly can ONLY be true for timeframe Ticks and >= Days !!
        if not self.componly and not self._barover(chkdata):
            return False

        # subdays: Ticks < (target-)timeframe < Days
        # subdays handled compressions itself in _barover?
        if self.subdays and self.p.bar2edge:
            return True
        elif not self.componly or not fromcheck:  # fromcheck doesn't increase compcount
            self.compcount += 1
            if not (self.compcount % self.p.compression):
                # boundary crossed and enough bars for compression ... proceed
                return True
            else:
                return False
        else:
            return False

    def _barover(self, data):
        """

        :param data:

        """
        tframe = self.p.timeframe

        if tframe == TimeFrame.Ticks:
            # Ticks is already the lowest level
            return self.bar.isopen()

        elif tframe < TimeFrame.Days:
            return self._barover_subdays(data)

        elif tframe == TimeFrame.Days:
            return self._barover_days(data)

        elif tframe == TimeFrame.Weeks:
            return self._barover_weeks(data)

        elif tframe == TimeFrame.Months:
            return self._barover_months(data)

        elif tframe == TimeFrame.Years:
            return self._barover_years(data)

    def _eosset(self):
        """ """
        if self._nexteos is None:
            self._nexteos, self._nextdteos = self.data._getnexteos()
            return

    def _eoscheck(self, data, seteos=True, exact=False, barovercond=False):
        """

        :param data:
        :param seteos:  (Default value = True)
        :param exact:  (Default value = False)
        :param barovercond:  (Default value = False)

        """
        if seteos:
            self._eosset()

        equal = data.datetime[0] == self._nextdteos
        grter = data.datetime[0] > self._nextdteos

        if exact:
            is_eos = equal
        else:
            # if the compared data goes over the endofsession
            # make sure the resampled bar is open and has something before that
            # end of session. It could be a weekend and nothing was delivered
            # until Monday
            if grter:
                is_eos = barovercond or (
                    self.bar.isopen() and self.bar.datetime <= self._nextdteos
                )
            else:
                is_eos = equal

        if is_eos:
            # we reached end of session, clear session so we fetch next eos
            self._lasteos = self._nexteos
            self._lastdteos = self._nextdteos
            self._nexteos = None
            self._nextdteos = float("-inf")

        return is_eos

    def _barover_days(self, data):
        """

        :param data:

        """
        return self._eoscheck(data)

    def _barover_weeks(self, data):
        """

        :param data:

        """
        if self.data._calendar is None:
            year, week, _ = data.num2date(self.bar.datetime).date().isocalendar()
            yearweek = year * 100 + week

            baryear, barweek, _ = data.datetime.date().isocalendar()
            bar_yearweek = baryear * 100 + barweek

            return bar_yearweek > yearweek
        else:
            return self.data._calendar.last_weekday(data.datetime.date())

    def _barover_months(self, data):
        """

        :param data:

        """
        dt = data.num2date(self.bar.datetime).date()
        yearmonth = dt.year * 100 + dt.month

        bardt = data.datetime.datetime()
        bar_yearmonth = bardt.year * 100 + bardt.month

        return bar_yearmonth > yearmonth

    def _barover_years(self, data):
        """

        :param data:

        """
        return data.datetime.datetime().year > data.num2date(self.bar.datetime).year

    def _gettmpoint(self, tm):
        """Returns the point of time intraday for a given time according to the
        timeframe

          - Ex 1: 00:05:00 in minutes -> point = 5
          - Ex 2: 00:05:20 in seconds -> point = 5 * 60 + 20 = 320

        :param tm:

        """
        point = tm.hour * 60 + tm.minute
        restpoint = 0

        if self.p.timeframe < TimeFrame.Minutes:
            point = point * 60 + tm.second

            if self.p.timeframe < TimeFrame.Seconds:
                point = point * 1e6 + tm.microsecond
            else:
                restpoint = tm.microsecond
        else:
            restpoint = tm.second + tm.microsecond

        point += self.p.boundoff

        return point, restpoint

    def _barover_subdays(self, data):
        """

        :param data:

        """
        if self._eoscheck(data):
            return True

        if data.datetime[0] < self.bar.datetime:
            return False

        # Get time objects for the comparisons - in utc-like format
        tm = num2date(self.bar.datetime).time()
        bartm = num2date(data.datetime[0]).time()

        point, _ = self._gettmpoint(tm)
        barpoint, _ = self._gettmpoint(bartm)

        ret = False
        if barpoint > point:
            # The data bar has surpassed the internal bar
            if not self.p.bar2edge:
                # Compression done on simple bar basis (like days)
                ret = True
            elif self.p.compression == 1:
                # no bar compression requested -> internal bar done
                ret = True
            else:
                point_comp = point // self.p.compression
                barpoint_comp = barpoint // self.p.compression

                # Went over boundary including compression
                if barpoint_comp > point_comp:
                    ret = True

        return ret

    def check(self, data, _forcedata=None):
        """Called to check if the current stored bar has to be delivered in
        spite of the data not having moved forward. If no ticks from a live
        feed come in, a 5 second resampled bar could be delivered 20 seconds
        later. When this method is called the wall clock (incl data time
        offset) is called to check if the time has gone so far as to have to
        deliver the already stored data

        :param data:
        :param _forcedata:  (Default value = None)

        """
        if not self.bar.isopen():
            return

        return self(data, fromcheck=True, forcedata=_forcedata)

    def _dataonedge(self, data):
        """

        :param data:

        """
        if not self.subweeks:
            if data._calendar is None:
                return False, True  # nothing can be done

            tframe = self.p.timeframe
            ret = False
            if tframe == TimeFrame.Weeks:  # Ticks is already the lowest
                ret = data._calendar.last_weekday(data.datetime.date())
            elif tframe == TimeFrame.Months:
                ret = data._calendar.last_monthday(data.datetime.date())
            elif tframe == TimeFrame.Years:
                ret = data._calendar.last_yearday(data.datetime.date())

            if ret:
                # Data must be consumed but compression may not be met yet
                # Prevent barcheckover from being called because it could again
                # increase compcount
                docheckover = False
                self.compcount += 1
                ret = not (self.compcount % self.p.compression)
            else:
                docheckover = True

            return ret, docheckover

        if self._eoscheck(data, exact=True):
            return True, True

        if self.subdays:
            point, prest = self._gettmpoint(data.datetime.time())
            if prest:
                return False, True  # cannot be on boundary, subunits present

            # Pass through compression to get boundary and rest over boundary
            bound, brest = divmod(point, self.p.compression)

            # if no extra and decomp bound is point
            return (brest == 0 and point == (bound * self.p.compression), True)

        # Code overriden by eoscheck
        if False and self.p.sessionend:
            # Days scenario - get datetime to compare in output timezone
            # because p.sessionend is expected in output timezone
            bdtime = data.datetime.datetime()
            bsend = datetime.combine(bdtime.date(), data.p.sessionend)
            return bdtime == bsend

        return False, True  # subweeks, not subdays and not sessionend

    def _calcadjtime(self, greater=False):
        """

        :param greater:  (Default value = False)

        """
        if self._nexteos is None:
            # Session has been exceeded - end of session is the mark
            return self._lastdteos  # utc-like

        dt = self.data.num2date(self.bar.datetime)

        # Get current time
        tm = dt.time()
        # Get the point of the day in the time frame unit (ex: minute 200)
        point, _ = self._gettmpoint(tm)

        # Apply compression to update the point position (comp 5 -> 200 // 5)
        # point = (point // self.p.compression)
        point = point // self.p.compression

        # If rightedge (end of boundary is activated) add it unless recursing
        point += self.p.rightedge

        # Restore point to the timeframe units by de-applying compression
        point *= self.p.compression

        # Get hours, minutes, seconds and microseconds
        extradays = 0
        if self.p.timeframe == TimeFrame.Minutes:
            ph, pm = divmod(point, 60)
            ps = 0
            pus = 0
        elif self.p.timeframe == TimeFrame.Seconds:
            ph, pm = divmod(point, 60 * 60)
            pm, ps = divmod(pm, 60)
            pus = 0
        elif self.p.timeframe <= TimeFrame.MicroSeconds:
            ph, pm = divmod(point, 60 * 60 * 1e6)
            pm, psec = divmod(pm, 60 * 1e6)
            ps, pus = divmod(psec, 1e6)
        elif self.p.timeframe == TimeFrame.Days:
            # last resort
            eost = self._nexteos.time()
            ph = eost.hour
            pm = eost.minute
            ps = eost.second
            pus = eost.microsecond

        if ph > 23:  # went over midnight:
            extradays = ph // 24
            ph %= 24

        # Replace intraday parts with the calculated ones and update it
        dt = dt.replace(
            hour=int(ph), minute=int(pm), second=int(ps), microsecond=int(pus)
        )
        if extradays:
            dt += timedelta(days=extradays)
        dtnum = self.data.date2num(dt)
        return dtnum

    def _adjusttime(self, greater=False, forcedata=None):
        """Adjusts the time of calculated bar (from underlying data source) by
        using the timeframe to the appropriate boundary, with compression taken
        into account

        Depending on param ``rightedge`` uses the starting boundary or the
        ending one

        :param greater:  (Default value = False)
        :param forcedata:  (Default value = None)

        """
        dtnum = self._calcadjtime(greater=greater)
        if greater and dtnum <= self.bar.datetime:
            return False

        self.bar.datetime = dtnum
        return True


class Resampler(_BaseResampler):
    """This class resamples data of a given timeframe to a larger timeframe."""

    params = (
        ("bar2edge", True),
        ("adjbartime", True),
        ("rightedge", True),
    )

    replaying = False

    def last(self, data):
        """Called when the data is no longer producing bars

        Can be called multiple times. It has the chance to (for example)
        produce extra bars which may still be accumulated and have to be
        delivered

        :param data:

        """
        if self.bar.isopen():
            if self.doadjusttime:
                self._adjusttime()

            data._add2stack(self.bar.lvalues())
            self.bar.bstart(maxdate=True)  # close the bar to avoid dups
            return True

        return False

    def __call__(self, data, fromcheck=False, forcedata=None):
        """Called for each set of values produced by the data source

        :param data:
        :param fromcheck:  (Default value = False)
        :param forcedata:  (Default value = None)

        """
        consumed = False
        onedge = False
        docheckover = True
        if not fromcheck:
            if self._latedata(data):
                if not self.p.takelate:
                    data.backwards()
                    return True  # get a new bar

                self.bar.bupdate(data)  # update new or existing bar
                # push time beyond reference
                self.bar.datetime = data.datetime[-1] + 0.000001
                data.backwards()  # remove used bar
                return True

            if self.componly:  # only if not subdays
                # Get a session ref before rewinding
                _, self._lastdteos = self.data._getnexteos()
                consumed = True

            else:
                onedge, docheckover = self._dataonedge(data)  # for subdays
                consumed = onedge

        if consumed:
            self.bar.bupdate(data)  # update new or existing bar
            if not self.componly:
                # eoscheck was possibly skipped in dataonedge so lets give it a
                # chance here
                self._eoscheck(data, barovercond=True)
            data.backwards()  # remove used bar

        # if self.bar.isopen and (onedge or (docheckover and checkbarover))
        cond = self.bar.isopen()
        if cond:  # original is and, the 2nd term must also be true
            if not onedge:  # onedge true is sufficient
                if docheckover:
                    cond = self._checkbarover(
                        data, fromcheck=fromcheck, forcedata=forcedata
                    )
        if cond:
            dodeliver = False
            if forcedata is not None:
                # check our delivery time is not larger than that of forcedata
                tframe = self.p.timeframe
                if tframe == TimeFrame.Ticks:  # Ticks is already the lowest
                    dodeliver = True
                elif tframe == TimeFrame.Minutes:
                    dtnum = self._calcadjtime(greater=True)
                    dodeliver = dtnum <= forcedata.datetime[0]
                elif tframe == TimeFrame.Days:
                    dtnum = self._calcadjtime(greater=True)
                    dodeliver = dtnum <= forcedata.datetime[0]
            else:
                dodeliver = True

            if dodeliver:
                if not onedge and self.doadjusttime:
                    self._adjusttime(greater=True, forcedata=forcedata)

                data._add2stack(self.bar.lvalues())
                self.bar.bstart(maxdate=True)  # bar delivered -> restart

        if not fromcheck:
            if not consumed:
                self.bar.bupdate(data)  # update new or existing bar
                data.backwards()  # remove used bar

        return True


class Replayer(_BaseResampler):
    """This class replays data of a given timeframe to a larger timeframe.

    It simulates the action of the market by slowly building up (for ex.) a
    daily bar from tick/seconds/minutes data

    Only when the bar is complete will the "length" of the data be changed
    effectively delivering a closed bar


    """

    params = (
        ("bar2edge", True),
        ("adjbartime", False),
        ("rightedge", True),
    )

    replaying = True

    def __call__(self, data, fromcheck=False, forcedata=None):
        """

        :param data:
        :param fromcheck:  (Default value = False)
        :param forcedata:  (Default value = None)

        """
        consumed = False
        onedge = False
        takinglate = False
        docheckover = True

        if not fromcheck:
            if self._latedata(data):
                if not self.p.takelate:
                    data.backwards(force=True)
                    return True  # get a new bar

                consumed = True
                takinglate = True

            elif self.componly:  # only if not subdays
                consumed = True

            else:
                onedge, docheckover = self._dataonedge(data)  # for subdays
                consumed = onedge

            data._tick_fill(force=True)  # update

        if consumed:
            self.bar.bupdate(data)
            if takinglate:
                self.bar.datetime = data.datetime[-1] + 0.000001

            # eoscheck was possibly skipped in dataonedge
            # so lets give it a chance here
            self._eoscheck(data)

        # if onedge or (checkbarover and self._checkbarover)
        cond = onedge
        if not cond:  # original is or, if true it would suffice
            if docheckover:
                cond = self._checkbarover(data, fromcheck=fromcheck)
        if cond:
            if not onedge and self.doadjusttime:  # insert tick with adjtime
                adjusted = self._adjusttime(greater=True)
                if adjusted:
                    ago = 0 if (consumed or fromcheck) else -1
                    # Update to the point right before the new data
                    data._updatebar(self.bar.lvalues(), forward=False, ago=ago)

                if not fromcheck:
                    if not consumed:
                        # Reopen bar with real new data and save data to queue
                        self.bar.bupdate(data, reopen=True)
                        # erase is True, but the tick will not be seen below
                        # and therefore no need to mark as 1st
                        data._save2stack(erase=True, force=True)
                    else:
                        self.bar.bstart(maxdate=True)
                        self._firstbar = True  # next is first
                else:  # from check
                    # fromcheck or consumed have  forced delivery, reopen
                    self.bar.bstart(maxdate=True)
                    self._firstbar = True  # next is first
                    if adjusted:
                        # after adjusting need to redeliver if this was a check
                        data._save2stack(erase=True, force=True)

            elif not fromcheck:
                if not consumed:
                    # Data already "forwarded" and we replay to new bar
                    # No need to go backwards. simply reopen internal cache
                    self.bar.bupdate(data, reopen=True)
                else:
                    # compression only, used data to update bar, hence remove
                    # from stream, update existing data, reopen bar
                    if not self._firstbar:  # only discard data if not firstbar
                        data.backwards(force=True)
                    data._updatebar(self.bar.lvalues(), forward=False, ago=0)
                    self.bar.bstart(maxdate=True)
                    self._firstbar = True  # make sure next tick moves forward

        elif not fromcheck:
            # not over, update, remove new entry, deliver
            if not consumed:
                self.bar.bupdate(data)

            if not self._firstbar:  # only discard data if not firstbar
                data.backwards(force=True)

            data._updatebar(self.bar.lvalues(), forward=False, ago=0)
            self._firstbar = False

        return False  # the existing bar can be processed by the system


class ResamplerTicks(Resampler):
    """ """

    params = (("timeframe", TimeFrame.Ticks),)


class ResamplerSeconds(Resampler):
    """ """

    params = (("timeframe", TimeFrame.Seconds),)


class ResamplerMinutes(Resampler):
    """ """

    params = (("timeframe", TimeFrame.Minutes),)


class ResamplerDaily(Resampler):
    """ """

    params = (("timeframe", TimeFrame.Days),)


class ResamplerWeekly(Resampler):
    """ """

    params = (("timeframe", TimeFrame.Weeks),)


class ResamplerMonthly(Resampler):
    """ """

    params = (("timeframe", TimeFrame.Months),)


class ResamplerYearly(Resampler):
    """ """

    params = (("timeframe", TimeFrame.Years),)


class ReplayerTicks(Replayer):
    """ """

    params = (("timeframe", TimeFrame.Ticks),)


class ReplayerSeconds(Replayer):
    """ """

    params = (("timeframe", TimeFrame.Seconds),)


class ReplayerMinutes(Replayer):
    """ """

    params = (("timeframe", TimeFrame.Minutes),)


class ReplayerDaily(Replayer):
    """ """

    params = (("timeframe", TimeFrame.Days),)


class ReplayerWeekly(Replayer):
    """ """

    params = (("timeframe", TimeFrame.Weeks),)


class ReplayerMonthly(Replayer):
    """ """

    params = (("timeframe", TimeFrame.Months),)
