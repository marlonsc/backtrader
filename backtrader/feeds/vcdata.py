"""vcdata.py module.

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

from datetime import datetime, timedelta, tzinfo

import backtrader as bt
from backtrader import TimeFrame, date2num
from backtrader.feed import DataBase
from backtrader.stores import vcstore
from backtrader.utils.py3 import (
    integer_types,
    queue,
    string_types,
    with_metaclass,
)


class MetaVCData(DataBase.__class__):
""""""
"""Class has already been created ... register

Args::
    name: 
    bases: 
    dct:"""
    dct:"""
        # Initialize the class
        super(MetaVCData, cls).__init__(name, bases, dct)

        # Register with the store
        vcstore.VCStore.DataCls = cls


class VCData(with_metaclass(MetaVCData, DataBase)):
    """VisualChart Data Feed."""

    params = (
        ("qcheck", 0.5),  # timeout in seconds (float) to check for events
        ("historical", False),  # usual industry value
        ("millisecond", True),  # fix missing millisecond in time
        ("tradename", None),  # name of the real asset to trade on
        ("usetimezones", True),  # use pytz timezones if found
    )

    # Holds the calculated offset to the timestamps of the VC Server
    _TOFFSET = timedelta()

    # States for the Finite State Machine in _load
    _ST_START, _ST_FEEDING, _ST_NOTFOUND = range(3)

    # Base NULL Date for VB/Excel date compatibility
    NULLDATE = datetime(1899, 12, 30, 0, 0, 0)

    # To correct HH:MM:59.999 times
    MILLISECOND = timedelta(microseconds=1000)

    # Large ping timeout
    PING_TIMEOUT = 25.0

    # Timezones for the different exchanges
    _TZS = {
        "Europe/London": (
            "011",
            "024",
            "027",
            "036",
            "049",
            "092",
            "114",
            # These are the global markets
            "033",
            "034",
            "035",
            "043",
            "054",
            "096",
            "300",
        ),
        "Europe/Berlin": (
            "005",
            "006",
            "008",
            "012",
            "013",
            "014",
            "015",
            "017",
            "019",
            "025",
            "029",
            "030",
            "037",
            "038",
            "052",
            "053",
            "060",
            "061",
            "072",
            "073",
            "074",
            "075",
            "080",
            "093",
            "094",
            "097",
            "111",
            "112",
            "113",
        ),
        "Asia/Tokyo": ("031",),
        "Australia/Melbourne": ("032",),
        "America/Argentina/Buenos_Aires": ("044",),
        "America/Sao_Paulo": ("045",),
        "America/Mexico_City": ("046",),
        "America/Santiago": ("047",),
        "US/Eastern": (
            "003",
            "004",
            "009",
            "010",
            "028",
            "040",
            "041",
            "055",
            "090",
            "095",
            "099",
        ),
        "US/Central": (
            "001",
            "002",
            "020",
            "021",
            "022",
            "023",
            "056",
        ),
    }

    # The global assets may have a different output timezoe
    _TZOUT = {
        "096.FTSE": "Europe/London",
        "096.FTEU3": "Europe/London",
        "096.MIB30": "Europe/Berlin",
        "096.SSMI": "Europe/Berlin",
        "096.HSI": "Asia/Hong_Kong",
        "096.BVSP": "America/Sao_Paulo",
        "096.MERVAL": "America/Argentina/Buenos_Aires",
        "096.DJI": "US/Eastern",
        "096.IXIC": "US/Eastern",
        "096.NDX": "US/Eastern",
    }

    # These global markets deliver data in local time dst adjuste unlike those
    # from above and need a readjustment
    _EXTRA_TIMEOFFSET = ("096",)

    _TIMEFRAME_BACKFILL = {
        TimeFrame.Ticks: timedelta(days=1),
        TimeFrame.MicroSeconds: timedelta(days=1),
        TimeFrame.Seconds: timedelta(days=1),
        TimeFrame.Minutes: timedelta(days=2),
        TimeFrame.Days: timedelta(days=365),
        TimeFrame.Weeks: timedelta(days=365 * 2),
        TimeFrame.Months: timedelta(days=365 * 5),
        TimeFrame.Years: timedelta(days=365 * 20),
    }

    def _timeoffset(self):
        """Returns the calculated time offset local equipment -> data server"""
        return self._TOFFSET

    def _gettzinput(self):
        """Returns the timezone to consider for the input data"""
        return self._gettz(tzin=True)

    def _gettz(self, tzin=False):
"""Returns the default output timezone for the data
This defaults to be the timezone in which the market is traded

Args::
    tzin: (Default value = False)"""
    tzin: (Default value = False)"""
        # If no object has been provided by the user and a timezone can be
        # found via contractdtails, then try to get it from pytz, which may or
        # may not be available.

        # The timezone specifications returned by TWS seem to be abbreviations
        # understood by pytz, but the full list which TWS may return is not
        # documented and one of the abbreviations may fail
        ptz = self.p.tz
        tzstr = isinstance(ptz, string_types)
        if ptz is not None and not tzstr:
            return bt.utils.date.Localizer(ptz)

        if self._state == self._ST_NOTFOUND:
            return None  # nothing else can be done

        if not self.p.usetimezones:
            return None

        try:
            import pytz  # keep the import very local
        except ImportError:
            return None  # nothing can be done

        # dataname 010ABCXXXXX -> ABC (3, 4 and 5) is market code
        if tzstr:
            tzs = ptz
        else:
            tzs = None

            if not tzin:
                if self.p.dataname in self._TZOUT:
                    tzs = self._TZOUT[self.p.dataname]

            if tzs is None:
                for mktz, mktcodes in self._TZS.items():
                    if self._mktcode in mktcodes:
                        tzs = mktz
                        break

            if tzs is None:
                return None

            if isinstance(tzs, tzinfo):
                return bt.utils.date.Localizer(tzs)

        if tzs:
            try:
                tz = pytz.timezone(tzs)
            except pytz.UnknownTimeZoneError:
                return None  # nothing can be done
        else:
            return None

        # contractdetails there, import ok, timezone found, return it
        return tz

    def islive(self):
"""Returns ``True`` to notify ``Cerebro`` that preloading and runonce
        should be deactivated"""
        """
        return True

    def __init__(self, **kwargs):
        """"""
        self.store = vcstore.VCStore(**kwargs)

        # Correct a copy past directly from VisualChart
        dataname = self.p.dataname
        if dataname[3].isspace():
            dataname = dataname[0:2] + dataname[4:]
            self.p.dataname = dataname

        self._dataname = "010" + self.p.dataname
        self._mktcode = self.p.dataname[0:3]

        self._tradename = tradename = self.p.tradename or self._dataname
        # Correct a copy past directly from VisualChart
        if tradename[3].isspace():
            tradename = tradename[0:2] + tradename[4:]
            self._tradename = tradename

    def setenvironment(self, env):
"""Receives an environment (cerebro) and passes it over to the store it
belongs to

Args::
    env:"""
    env:"""
        super(VCData, self).setenvironment(env)
        env.addstore(self.store)

    def start(self):
"""Starts the VC connecction and gets the real contract and
        contractdetails if it exists"""
        """
        super(VCData, self).start()

        self._state = self._ST_START  # mini finite state machine

        self._newticks = True  # control processing of initial ticks

        self._pingtmout = self.PING_TIMEOUT  # Initial timeout for ping

        self.idx = 1  # counter for the dataserie (vb is based at 1)
        self.q = None  # where bars are received

        # market time offsets
        self._mktoffset = None
        self._mktoff1 = None
        self._mktoffdiff = None

        if not self.store.connected():
            # Not connected -> go away
            self.put_notification(self.DISCONNECTED)
            self._state = self._ST_NOTFOUND
            return

        self.put_notification(self.CONNECTED)
        # get real contract details with real conId (contractId)
        self.qrt = queue.Queue()  # to await a ping
        self.store._rtdata(self, self._dataname)
        symfound = self.qrt.get()
        if not symfound:
            # Kill any further action and signal it
            self.put_notification(self.NOTSUBSCRIBED)
            self.put_notification(self.DISCONNECTED)
            self._state = self._ST_NOTFOUND
            return

        if self.replaying:
            # In this case don't request the final
            # timeframe from vc, but the original that has to be replayed
            self._tf, self._comp = self.p.timeframe, self.p.compression
        else:
            # Else (even if resampling) pass the final timeframe which may
            # been modified by a resampling filter
            self._tf, self._comp = (
                self._timeframe,
                self._compression,
            )

        self._ticking = self.store._ticking(self._tf)
        self._syminfo = syminfo = self.store._symboldata(self._dataname)

        # For most markets:
        # mktoffset == mktoff1 and substracting this value from reported times
        # is enough to report the "market time". Visual Chart changes this from
        # a value X to 0 if the appropriate setting in the GUI is changed to
        # change display of time from local <-> market
        #
        # But some markets (at least 096XXX) that theoretically live in
        # Europe/London seem to be displaced 1 hour to the west and an extra
        # hour is needed.
        # These markets do also need "usetimezoned" True to actually display
        # the market time, because this is done internally using the
        # definitions in TZOUTS

        # Record and calculate market offsets
        self._mktoffset = timedelta(seconds=syminfo.TimeOffset)
        # Add millisecond to pusth HH:MM:59.999 -> 00.000 unless ticks
        if self.p.millisecond and not self._ticking:
            self._mktoffset -= self.MILLISECOND

        self._mktoff1 = self._mktoffset
        if self._mktcode in self._EXTRA_TIMEOFFSET:
            # These codes live theoretically in
            # (UTC+00:00) Dublin, Edinburgh, Lisbon, London which is
            # 'Europe/London'
            # But all experiments show the times to be displaced 1 hour to
            # the west and hence the extra 3600 seconds
            self._mktoffset -= timedelta(seconds=3600)

        self._mktoffdiff = self._mktoffset - self._mktoff1

        if self._state == self._ST_START:
            self.put_notification(self.DELAYED)

            # Now request the data and get a comms queue for it
            self.q = self.store._directdata(
                self,
                self._dataname,
                self._tf,
                self._comp,
                self.p.fromdate,
                self.p.todate,
                self.p.historical,
            )

            self._state = self._ST_FEEDING

    def stop(self):
        """Stops and tells the store to stop"""
        super(VCData, self).stop()
        if self.q:
            self.store._canceldirectdata(self.q)

    def _setserie(self, serie):
"""Args::
    serie:"""
""""""
""""""
"""Returns the actual ping timeout for PumpEvents to wake up and call
        ping, which will check if the not yet delivered bar can be
        delivered. The bar may be stalled because vc awaits a new tick and
        during low negotiation hour this can take several seconds after the
        actual expected delivery time"""
        """
        if self._ticking:
            return -1  # no timeout

        return self._pingtmout

    def OnNewDataSerieBar(self, DataSerie, forcepush=False):
"""Args::
    DataSerie: 
    forcepush: (Default value = False)"""
    forcepush: (Default value = False)"""
        # Processes the COM Event (also called directly when 1st creating the
        # data serie
        ssize = DataSerie.Size

        if ssize - self.idx > 1:
            # More than 1 bar on-board -> delay in place
            if self._laststatus != self.DELAYED:
                self.q.put(self.store._RT_DELAYED)

        # return everything if original tf is ticks or force pushing
        ssize += forcepush or self._ticking
        for idx in range(self.idx, ssize):
            bar = DataSerie.GetBarValues(idx)
            self.q.put(bar)

        if not forcepush and not self._ticking and ssize:
            # A bar has been left in place
            dtnow = datetime.now() - self._TOFFSET  # adjust local time

            bar = DataSerie.GetBarValues(ssize)
            dt = self.NULLDATE + timedelta(days=bar.Date) - self._mktoffdiff
            if dtnow < dt:
                # A bar is there, not deliverable yet - LIVE
                if self._laststatus != self.LIVE:
                    self.q.put(self.store._RT_LIVE)

                # Adjust ping timeout to the bar boundary (plus mini leeway)
                self._pingtmout = (dt - dtnow).total_seconds() + 0.5

            else:
                self._pingtmout = self.PING_TIMEOUT  # no bar left, long pause
                self.q.put(bar)  # push bar and update index
                ssize += 1  # pushed last one out

        # Write down the last processed bar
        self.idx = max(1, ssize)

    def ping(self):
""""""
"""Args::
    p1: 
    p2: 
    p3:"""
    p3:"""
            if p1 != 1:  # Apparently "Connection Event"
                return

            if p2 == self.lastconn:
                return  # do not notify twice

            self.lastconn = p2  # keep new notification code

            # p2 should be 0 (disconn), 1 (conn)
            self.store._vcrt_connection(self.store._RT_BASEMSG - p2)

    def OnNewTicks(self, ArrayTicks):
"""Args::
    ArrayTicks:"""
"""Args::
    ticks:"""
    ticks:"""
        print("*" * 50, "DEBUG OnNewTicks")
        for tick in ticks:
            print("-" * 40)
            print("tick.SymbolCode", tick.SymbolCode.encode("ascii", "ignore"))
            fname = self.store.vcrtfields.get(tick.Field, tick.Field)
            print("  tick.Field   : {} ({})".format(fname, tick.Field))
            print("  tick.FieldEx :", tick.FieldEx)
            tdate = tick.Date
            if tdate:
                tdate = self.NULLDATE + timedelta(days=tick.Date)
            print("  tick.Date    :", tdate)

            print("  tick.Index   :", tick.TickIndex)
            print("  tick.Value   :", tick.Value)
            print("  tick.Text    :", tick.Text.encode("ascii", "ignore"))
