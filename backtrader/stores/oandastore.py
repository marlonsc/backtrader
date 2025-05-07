"""oandastore.py module.

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

import collections
import json
import threading
import time as _time
from datetime import datetime, timedelta

import backtrader as bt
import oandapy
import requests  # oandapy depdendency
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import queue, with_metaclass

# Extend the exceptions to support extra cases


class OandaRequestError(oandapy.OandaError):
""""""
""""""
""""""
"""Args::
    content: (Default value = "")"""
""""""
"""Args::
    content:"""
""""""
""""""
""""""
"""Args::
    endpoint: 
    method: (Default value = "GET")
    params: (Default value = None)"""
    params: (Default value = None)"""
        # Overriden to make something sensible out of a
        # request.RequestException rather than simply issuing a print(str(e))
        url = "%s/%s" % (self.api_url, endpoint)

        method = method.lower()
        params = params or {}

        func = getattr(self.client, method)

        request_args = {}
        if method == "get":
            request_args["params"] = params
        else:
            request_args["data"] = params

        # Added the try block
        try:
            response = func(url, **request_args)
        except requests.RequestException:
            return OandaRequestError().error_response

        content = response.content.decode("utf-8")
        content = json.loads(content)

        # error message
        if response.status_code >= 400:
            # changed from raise to return
            return oandapy.OandaError(content).error_response

        return content


class Streamer(oandapy.Streamer):
""""""
"""Args::
    q: 
    headers: (Default value = None)"""
    headers: (Default value = None)"""
        # Override to provide headers, which is in the standard API interface
        super(Streamer, self).__init__(*args, **kwargs)

        if headers:
            self.client.headers.update(headers)

        self.q = q

    def run(self, endpoint, params=None):
"""Args::
    endpoint: 
    params: (Default value = None)"""
    params: (Default value = None)"""
        # Override to better manage exceptions.
        # Kept as much as possible close to the original
        self.connected = True

        params = params or {}

        ignore_heartbeat = None
        if "ignore_heartbeat" in params:
            ignore_heartbeat = params["ignore_heartbeat"]

        request_args = {}
        request_args["params"] = params

        url = "%s/%s" % (self.api_url, endpoint)

        while self.connected:
            # Added exception control here
            try:
                response = self.client.get(url, **request_args)
            except requests.RequestException:
                self.q.put(OandaRequestError().error_response)
                break

            if response.status_code != 200:
                self.on_error(response.content)
                break  # added break here

            # Changed chunk_size 90 -> None
            try:
                for line in response.iter_lines(chunk_size=None):
                    if not self.connected:
                        break

                    if line:
                        data = json.loads(line.decode("utf-8"))
                        if not (ignore_heartbeat and "heartbeat" in data):
                            self.on_success(data)

            except BaseException:  # socket.error has been seen
                self.q.put(OandaStreamError().error_response)
                break

    def on_success(self, data):
"""Args::
    data:"""
"""Args::
    data:"""
    """Metaclass to make a metaclassed class a singleton"""

    def __init__(cls, name, bases, dct):
"""Args::
    name: 
    bases: 
    dct:"""
    dct:"""
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        """"""
        if cls._singleton is None:
            cls._singleton = super(MetaSingleton, cls).__call__(*args, **kwargs)

        return cls._singleton


class OandaStore(with_metaclass(MetaSingleton, object)):
    """Singleton class wrapping to control the connections to Oanda."""

    BrokerCls = None  # broker class will autoregister
    DataCls = None  # data class will auto register

    params = (
        ("token", ""),
        ("account", ""),
        ("practice", False),
        ("account_tmout", 10.0),  # account balance refresh timeout
    )

    _DTEPOCH = datetime(1970, 1, 1)
    _ENVPRACTICE = "practice"
    _ENVLIVE = "live"

    @classmethod
    def getdata(cls, *args, **kwargs):
        """Returns ``DataCls`` with args, kwargs"""
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        """Returns broker with *args, **kwargs from registered ``BrokerCls``"""
        return cls.BrokerCls(*args, **kwargs)

    def __init__(self):
""""""
"""Args::
    data: (Default value = None)
    broker: (Default value = None)"""
    broker: (Default value = None)"""
        # Datas require some processing to kickstart data reception
        if data is None and broker is None:
            self.cash = None
            return

        if data is not None:
            self._env = data._env
            # For datas simulate a queue with None to kickstart co
            self.datas.append(data)

            if self.broker is not None:
                self.broker.data_started(data)

        elif broker is not None:
            self.broker = broker
            self.streaming_events()
            self.broker_threads()

    def stop(self):
""""""
"""Args::
    msg:"""
""""""
""""""
"""Args::
    timeframe: 
    compression:"""
    compression:"""
        return self._GRANULARITIES.get((timeframe, compression), None)

    def get_instrument(self, dataname):
"""Args::
    dataname:"""
"""Args::
    tmout: (Default value = None)"""
"""Args::
    q: 
    tmout: (Default value = None)"""
    tmout: (Default value = None)"""
        while True:
            trans = q.get()
            self._transaction(trans)

    def _t_streaming_events(self, q, tmout=None):
"""Args::
    q: 
    tmout: (Default value = None)"""
    tmout: (Default value = None)"""
        if tmout is not None:
            _time.sleep(tmout)

        streamer = Streamer(
            q,
            environment=self._oenv,
            access_token=self.p.token,
            headers={"X-Accept-Datetime-Format": "UNIX"},
        )

        streamer.events(ignore_heartbeat=False)

    def candles(
        self,
        dataname,
        dtbegin,
        dtend,
        timeframe,
        compression,
        candleFormat,
        includeFirst,
    ):
"""Args::
    dataname: 
    dtbegin: 
    dtend: 
    timeframe: 
    compression: 
    candleFormat: 
    includeFirst:"""
    includeFirst:"""

        kwargs = locals().copy()
        kwargs.pop("self")
        kwargs["q"] = q = queue.Queue()
        t = threading.Thread(target=self._t_candles, kwargs=kwargs)
        t.daemon = True
        t.start()
        return q

    def _t_candles(
        self,
        dataname,
        dtbegin,
        dtend,
        timeframe,
        compression,
        candleFormat,
        includeFirst,
        q,
    ):
"""Args::
    dataname: 
    dtbegin: 
    dtend: 
    timeframe: 
    compression: 
    candleFormat: 
    includeFirst: 
    q:"""
    q:"""

        granularity = self.get_granularity(timeframe, compression)
        if granularity is None:
            e = OandaTimeFrameError()
            q.put(e.error_response)
            return

        dtkwargs = {}
        if dtbegin is not None:
            dtkwargs["start"] = int((dtbegin - self._DTEPOCH).total_seconds())

        if dtend is not None:
            dtkwargs["end"] = int((dtend - self._DTEPOCH).total_seconds())

        try:
            response = self.oapi.get_history(
                instrument=dataname,
                granularity=granularity,
                candleFormat=candleFormat,
                **dtkwargs,
            )

        except oandapy.OandaError as e:
            q.put(e.error_response)
            q.put(None)
            return

        for candle in response.get("candles", []):
            q.put(candle)

        q.put({})  # end of transmission

    def streaming_prices(self, dataname, tmout=None):
"""Args::
    dataname: 
    tmout: (Default value = None)"""
    tmout: (Default value = None)"""
        q = queue.Queue()
        kwargs = {"q": q, "dataname": dataname, "tmout": tmout}
        t = threading.Thread(target=self._t_streaming_prices, kwargs=kwargs)
        t.daemon = True
        t.start()
        return q

    def _t_streaming_prices(self, dataname, q, tmout):
"""Args::
    dataname: 
    q: 
    tmout:"""
    tmout:"""
        if tmout is not None:
            _time.sleep(tmout)

        streamer = Streamer(
            q,
            environment=self._oenv,
            access_token=self.p.token,
            headers={"X-Accept-Datetime-Format": "UNIX"},
        )

        streamer.rates(self.p.account, instruments=dataname)

    def get_cash(self):
""""""
""""""
""""""
""""""
"""Args::
    order: 
    stopside: (Default value = None)
    takeside: (Default value = None)"""
    takeside: (Default value = None)"""
        okwargs = dict()
        okwargs["instrument"] = order.data._dataname
        okwargs["units"] = abs(order.created.size)
        okwargs["side"] = "buy" if order.isbuy() else "sell"
        okwargs["type"] = self._ORDEREXECS[order.exectype]
        if order.exectype != bt.Order.Market:
            okwargs["price"] = order.created.price
            if order.valid is None:
                # 1 year and datetime.max fail ... 1 month works
                valid = datetime.utcnow() + timedelta(days=30)
            else:
                valid = order.data.num2date(order.valid)
                # To timestamp with seconds precision
            okwargs["expiry"] = int((valid - self._DTEPOCH).total_seconds())

        if order.exectype == bt.Order.StopLimit:
            okwargs["lowerBound"] = order.created.pricelimit
            okwargs["upperBound"] = order.created.pricelimit

        if order.exectype == bt.Order.StopTrail:
            okwargs["trailingStop"] = order.trailamount

        if stopside is not None:
            okwargs["stopLoss"] = stopside.price

        if takeside is not None:
            okwargs["takeProfit"] = takeside.price

        okwargs.update(**kwargs)  # anything from the user

        self.q_ordercreate.put(
            (
                order.ref,
                okwargs,
            )
        )
        return order

    _OIDSINGLE = ["orderOpened", "tradeOpened", "tradeReduced"]
    _OIDMULTIPLE = ["tradesClosed"]

    def _t_order_create(self):
""""""
"""Args::
    order:"""
""""""
"""Args::
    trans:"""
"""Args::
    oid: 
    trans:"""
    trans:"""
        try:
            oref = self._ordersrev.pop(oid)
        except KeyError:
            return

        ttype = trans["type"]

        if ttype in self._X_ORDER_FILLED:
            size = trans["units"]
            if trans["side"] == "sell":
                size = -size
            price = trans["price"]
            self.broker._fill(oref, size, price, ttype=ttype)

        elif ttype in self._X_ORDER_CREATE:
            self.broker._accept(oref)
            self._ordersrev[oid] = oref

        elif ttype in "ORDER_CANCEL":
            reason = trans["reason"]
            if reason == "ORDER_FILLED":
                pass  # individual execs have done the job
            elif reason == "TIME_IN_FORCE_EXPIRED":
                self.broker._expire(oref)
            elif reason == "CLIENT_REQUEST":
                self.broker._cancel(oref)
            else:  # default action ... if nothing else
                self.broker._reject(oref)
