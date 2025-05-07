"""oanda.py module.

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

from backtrader import date2num, num2date
from backtrader.feed import DataBase
from backtrader.stores import oandastore
from backtrader.utils.py3 import (
    queue,
    with_metaclass,
)


class MetaOandaData(DataBase.__class__):
""""""
"""Class has already been created ... register

Args::
    name: 
    bases: 
    dct:"""
    dct:"""
        # Initialize the class
        super(MetaOandaData, cls).__init__(name, bases, dct)

        # Register with the store
        oandastore.OandaStore.DataCls = cls


class OandaData(with_metaclass(MetaOandaData, DataBase)):
    """Oanda Data Feed."""

    params = (
        ("qcheck", 0.5),
        ("historical", False),  # do backfilling at the start
        ("backfill_start", True),  # do backfilling at the start
        ("backfill", True),  # do backfilling when reconnecting
        ("backfill_from", None),  # additional data source to do backfill from
        ("bidask", True),
        ("useask", False),
        ("includeFirst", True),
        ("reconnect", True),
        ("reconnections", -1),  # forever
        ("reconntimeout", 5.0),
    )

    _store = oandastore.OandaStore

    # States for the Finite State Machine in _load
    _ST_FROM, _ST_START, _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(5)

    _TOFFSET = timedelta()

    def _timeoffset(self):
""""""
"""Returns ``True`` to notify ``Cerebro`` that preloading and runonce
        should be deactivated"""
        """
        return True

    def __init__(self, **kwargs):
        """"""
        self.o = self._store(**kwargs)
        self._candleFormat = "bidask" if self.p.bidask else "midpoint"

    def setenvironment(self, env):
"""Receives an environment (cerebro) and passes it over to the store it
belongs to

Args::
    env:"""
    env:"""
        super(OandaData, self).setenvironment(env)
        env.addstore(self.o)

    def start(self):
"""Starts the Oanda connecction and gets the real contract and
        contractdetails if it exists"""
        """
        super(OandaData, self).start()

        # Create attributes as soon as possible
        self._statelivereconn = False  # if reconnecting in live state
        self._storedmsg = dict()  # keep pending live message (under None)
        self.qlive = queue.Queue()
        self._state = self._ST_OVER

        # Kickstart store and get queue to wait on
        self.o.start(data=self)

        # check if the granularity is supported
        otf = self.o.get_granularity(self._timeframe, self._compression)
        if otf is None:
            self.put_notification(self.NOTSUPPORTED_TF)
            self._state = self._ST_OVER
            return

        self.contractdetails = cd = self.o.get_instrument(self.p.dataname)
        if cd is None:
            self.put_notification(self.NOTSUBSCRIBED)
            self._state = self._ST_OVER
            return

        if self.p.backfill_from is not None:
            self._state = self._ST_FROM
            self.p.backfill_from._start()
        else:
            self._start_finish()
            self._state = self._ST_START  # initial state for _load
            self._st_start()

        self._reconns = 0

    def _st_start(self, instart=True, tmout=None):
"""Args::
    instart: (Default value = True)
    tmout: (Default value = None)"""
    tmout: (Default value = None)"""
        if self.p.historical:
            self.put_notification(self.DELAYED)
            dtend = None
            if self.todate < float("inf"):
                dtend = num2date(self.todate)

            dtbegin = None
            if self.fromdate > float("-inf"):
                dtbegin = num2date(self.fromdate)

            self.qhist = self.o.candles(
                self.p.dataname,
                dtbegin,
                dtend,
                self._timeframe,
                self._compression,
                candleFormat=self._candleFormat,
                includeFirst=self.p.includeFirst,
            )

            self._state = self._ST_HISTORBACK
            return True

        self.qlive = self.o.streaming_prices(self.p.dataname, tmout=tmout)
        if instart:
            self._statelivereconn = self.p.backfill_start
        else:
            self._statelivereconn = self.p.backfill

        if self._statelivereconn:
            self.put_notification(self.DELAYED)

        self._state = self._ST_LIVE
        if instart:
            self._reconns = self.p.reconnections

        return True  # no return before - implicit continue

    def stop(self):
        """Stops and tells the store to stop"""
        super(OandaData, self).stop()
        self.o.stop()

    def haslivedata(self):
""""""
""""""
"""Args::
    msg:"""
"""Args::
    msg:"""
    msg:"""
        dtobj = datetime.utcfromtimestamp(int(msg["time"]) / 10**6)
        dt = date2num(dtobj)
        if dt <= self.lines.datetime[-1]:
            return False  # time already seen

        # Common fields
        self.lines.datetime[0] = dt
        self.lines.volume[0] = float(msg["volume"])
        self.lines.openinterest[0] = 0.0

        # Put the prices into the bar
        if self.p.bidask:
            if not self.p.useask:
                self.lines.open[0] = float(msg["openBid"])
                self.lines.high[0] = float(msg["highBid"])
                self.lines.low[0] = float(msg["lowBid"])
                self.lines.close[0] = float(msg["closeBid"])
            else:
                self.lines.open[0] = float(msg["openAsk"])
                self.lines.high[0] = float(msg["highAsk"])
                self.lines.low[0] = float(msg["lowAsk"])
                self.lines.close[0] = float(msg["closeAsk"])
        else:
            self.lines.open[0] = float(msg["openMid"])
            self.lines.high[0] = float(msg["highMid"])
            self.lines.low[0] = float(msg["lowMid"])
            self.lines.close[0] = float(msg["closeMid"])

        return True
