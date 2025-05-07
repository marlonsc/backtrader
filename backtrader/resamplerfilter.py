"""resamplerfilter.py module.

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

from datetime import datetime, timedelta

from . import metabase
from .dataseries import TimeFrame, _Bar
from .utils.date import date2num, num2date
from .utils.py3 import with_metaclass


class DTFaker(object):
""""""
"""Args::
    data: 
    forcedata: (Default value = None)"""
    forcedata: (Default value = None)"""
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
""""""
"""Args::
    idx: (Default value = 0)"""
"""Args::
    idx: (Default value = 0)"""
"""Args::
    idx: (Default value = 0)"""
"""Args::
    idx: (Default value = 0)"""
""""""
"""Args::
    idx:"""
        """"""
        return self.data.num2date(*args, **kwargs)

    def date2num(self, *args, **kwargs):
        """"""
        return self.data.date2num(*args, **kwargs)

    def _getnexteos(self):
""""""
"""Base class for all resamplers and replayers. Handles parameter access and
    ensures all required attributes are present. All docstrings and comments must be
    line-wrapped at 90 characters or less."""
    """

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

    replaying = False

    def __init__(self, data):
"""Args::
    data:"""
""""""
"""Args::
    data:"""
"""Args::
    data: 
    fromcheck: (Default value = False)
    forcedata: (Default value = None)"""
    forcedata: (Default value = None)"""
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
"""Args::
    data:"""
""""""
"""Args::
    data: 
    seteos: (Default value = True)
    exact: (Default value = False)
    barovercond: (Default value = False)"""
    barovercond: (Default value = False)"""
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
"""Args::
    data:"""
"""Args::
    data:"""
"""Args::
    data:"""
"""Args::
    data:"""
"""Returns the point of time intraday for a given time according to the
timeframe
- Ex 1: 00:05:00 in minutes -> point = 5
- Ex 2: 00:05:20 in seconds -> point = 5 * 60 + 20 = 320

Args::
    tm:"""
    tm:"""
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
"""Args::
    data:"""
"""Called to check if the current stored bar has to be delivered in
spite of the data not having moved forward. If no ticks from a live
feed come in, a 5 second resampled bar could be delivered 20 seconds
later. When this method is called the wall clock (incl data time
offset) is called to check if the time has gone so far as to have to
deliver the already stored data

Args::
    data: 
    _forcedata: (Default value = None)"""
    _forcedata: (Default value = None)"""
        if not self.bar.isopen():
            return
        # The following line previously called self() which is not callable.
        # Manual review required for correct logic.
        # return self(data, fromcheck=True, forcedata=_forcedata)
        # TODO: Manual review required for correct logic.
        return None

    def _dataonedge(self, data):
"""Args::
    data:"""
"""Returns the point of time intraday for a given time according to the timeframe.

Args::
    greater: (Default value = False)"""
    greater: (Default value = False)"""
        if self._nexteos is None:
            # Session has been exceeded - end of session is the mark
            return self._lastdteos  # utc-like
        dt = self.data.num2date(self.bar.datetime)
        # Get current time
        tm = dt.time()
        # Get the point of the day in the time frame unit (ex: minute 200)
        point, _ = self._gettmpoint(tm)
        # Apply compression to update the point position (comp 5 -> 200 // 5)
        point = point // self.p.compression
        # If rightedge (end of boundary is activated) add it unless recursing
        point += self.p.rightedge
        # Restore point to the timeframe units by de-applying compression
        point *= self.p.compression
        # Get hours, minutes, seconds and microseconds
        extradays = 0
        ph = pm = ps = pus = 0  # Ensure all variables are initialized
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

Args::
    greater: (Default value = False)
    forcedata: (Default value = None)"""
    forcedata: (Default value = None)"""
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

Args::
    data:"""
    data:"""
        if self.bar.isopen():
            if self.doadjusttime:
                self._adjusttime()

            data._add2stack(self.bar.lvalues())
            self.bar.bstart(maxdate=True)  # close the bar to avoid dups
            return True

        return False

    def __call__(self, data, fromcheck=False, forcedata=None):
"""Called for each set of values produced by the data source

Args::
    data: 
    fromcheck: (Default value = False)
    forcedata: (Default value = None)"""
    forcedata: (Default value = None)"""
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
effectively delivering a closed bar"""

    params = (
        ("bar2edge", True),
        ("adjbartime", False),
        ("rightedge", True),
    )

    replaying = True

    def __call__(self, data, fromcheck=False, forcedata=None):
"""Args::
    data: 
    fromcheck: (Default value = False)
    forcedata: (Default value = None)"""
    forcedata: (Default value = None)"""
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
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""

    params = (("timeframe", TimeFrame.Months),)
