"""vcstore.py module.

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
import ctypes
import os.path
import threading
from datetime import datetime, timedelta

from backtrader import TimeFrame
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import (
    queue,
    with_metaclass,
)


class _SymInfo(object):
""""""
"""Args::
    syminfo:"""
"""This following code waits for 'timeout' seconds in the way
required for COM, internally doing the correct things depending
on the COM appartment of the current thread.  It is possible to
terminate the message loop by pressing CTRL+C, which will raise
a KeyboardInterrupt.

Args::
    timeout: (Default value = -1)
    hevt: (Default value = None)
    cb: (Default value = None)"""
    cb: (Default value = None)"""
    # XXX Should there be a way to pass additional event handles which
    # can terminate this function?

    # XXX XXX XXX
    #
    # It may be that I misunderstood the CoWaitForMultipleHandles
    # function.  Is a message loop required in a STA?  Seems so...
    #
    # MSDN says:
    #
    # If the caller resides in a single-thread apartment,
    # CoWaitForMultipleHandles enters the COM modal loop, and the
    # thread's message loop will continue to dispatch messages using
    # the thread's message filter. If no message filter is registered
    # for the thread, the default COM message processing is used.
    #
    # If the calling thread resides in a multithread apartment (MTA),
    # CoWaitForMultipleHandles calls the Win32 function
    # MsgWaitForMultipleObjects.

    # Timeout expected as float in seconds - *1000 to miliseconds
    # timeout = -1 -> INFINITE 0xFFFFFFFF;
    # It can also be a callable which should return an amount in seconds

    if hevt is None:
        hevt = ctypes.windll.kernel32.CreateEventA(None, True, False, None)

    handles = _handles_type(hevt)
    RPC_S_CALLPENDING = -2147417835

    # @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)
    def HandlerRoutine(dwCtrlType):
"""Args::
    dwCtrlType:"""
""""""
"""Args::
    store:"""
"""Args::
    ArrayTicks:"""
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


class MetaSingleton(MetaParams):
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


class VCStore(with_metaclass(MetaSingleton, object)):
    """Singleton class wrapping an ibpy ibConnection instance.
The parameters can also be specified in the classes which use this store,
like ``VCData`` and ``VCBroker``"""

    BrokerCls = None  # broker class will autoregister
    DataCls = None  # data class will auto register

    # 32 bit max unsigned int for openinterest correction
    MAXUINT = 0xFFFFFFFF // 2

    # to remove at least 1 sec or else there seem to be internal conv problems
    MAXDATE1 = datetime.max - timedelta(days=1, seconds=1)
    MAXDATE2 = datetime.max - timedelta(seconds=1)

    _RT_SHUTDOWN = -0xFFFF
    _RT_BASEMSG = -0xFFF0
    _RT_DISCONNECTED = -0xFFF0
    _RT_CONNECTED = -0xFFF1
    _RT_LIVE = -0xFFF2
    _RT_DELAYED = -0xFFF3
    _RT_TYPELIB = -0xFFE0
    _RT_TYPEOBJ = -0xFFE1
    _RT_COMTYPES = -0xFFE2

    @classmethod
    def getdata(cls, *args, **kwargs):
        """Returns ``DataCls`` with args, kwargs"""
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        """Returns broker with *args, **kwargs from registered ``BrokerCls``"""
        return cls.BrokerCls(*args, **kwargs)

    # DLLs to parse if found for TypeLibs
    VC64_DLLS = (
        "VCDataSource64.dll",
        "VCRealTimeLib64.dll",
        "COMTraderInterfaces64.dll",
    )

    VC_DLLS = (
        "VCDataSource.dll",
        "VCRealTimeLib.dll",
        "COMTraderInterfaces.dll",
    )

    # Well known CLSDI
    VC_TLIBS = (
        ["{EB2A77DC-A317-4160-8833-DECF16275A05}", 1, 0],  # vcdatasource64
        ["{86F1DB04-2591-4866-A361-BB053D77FA18}", 1, 0],  # vcrealtime64
        ["{20F8873C-35BE-4DB4-8C2A-0A8D40F8AEC3}", 1, 0],  # raderinterface64
    )

    VC_KEYNAME = r"SOFTWARE\VCG\Visual Chart 6\Config"
    VC_KEYVAL = "Directory"
    VC_BINPATH = "bin"

    def find_vchart(self):
""""""
""""""
""""""
"""Args::
    msg:"""
""""""
"""Args::
    data: (Default value = None)
    broker: (Default value = None)"""
    broker: (Default value = None)"""
        if not self._connected:
            return

        if self.t_vcconn is None:
            # Kickstart connection thread check
            self.t_vcconn = t = threading.Thread(target=self._start_vcrt)
            t.daemon = True  # Do not stop a general exit
            t.start()

        if broker is not None:
            t = threading.Thread(target=self._t_broker, args=(broker,))
            t.daemon = True
            t.start()

    def stop(self):
""""""
""""""
""""""
"""Args::
    status:"""
"""Args::
    timeframe: 
    compression:"""
    compression:"""
        # Translates timeframes to known compression types in VisualChart
        timeframe, extracomp = self._tftable[timeframe]
        return timeframe, compression * extracomp

    def _ticking(self, timeframe):
"""Args::
    timeframe:"""
"""Args::
    data:"""
"""Args::
    q:"""
"""Args::
    data: 
    symbol:"""
    symbol:"""
        kwargs = dict(data=data, symbol=symbol)
        t = threading.Thread(target=self._t_rtdata, kwargs=kwargs)
        t.daemon = True
        t.start()

    # Broker functions
    def _t_rtdata(self, data, symbol):
"""Args::
    data: 
    symbol:"""
    symbol:"""
        self.comtypes.CoInitialize()  # running in another thread
        vcrt = self.CreateObject(self.vcrtmod.RealTime)
        conn = self.GetEvents(vcrt, data)
        data._vcrt = vcrt
        vcrt.RequestSymbolFeed(symbol, False)  # no limits
        PumpEvents()
        del conn  # ensure events go away
        self.comtypes.CoUninitialize()

    def _symboldata(self, symbol):
"""Args::
    symbol:"""
"""Args::
    q:"""
"""Args::
    data: 
    symbol: 
    timeframe: 
    compression: 
    d1: 
    d2: (Default value = None)
    historical: (Default value = False)"""
    historical: (Default value = False)"""

        # Assume the data has checked the existence of the symbol
        timeframe, compression = self._tf2ct(timeframe, compression)
        kwargs = locals().copy()  # make a copy of the args
        kwargs.pop("self")
        kwargs["q"] = q = self._getq(data)

        t = threading.Thread(target=self._t_directdata, kwargs=kwargs)
        t.daemon = True
        t.start()

        # use the queue to synchronize until symbolinfo has been gotten
        return q  # tell the caller where to expect the hist data

    def _t_directdata(
        self, data, symbol, timeframe, compression, d1, d2, q, historical
    ):
"""Args::
    data: 
    symbol: 
    timeframe: 
    compression: 
    d1: 
    d2: 
    q: 
    historical:"""
    historical:"""

        self.comtypes.CoInitialize()  # start com threading
        vcds = self.CreateObject(self.vcdsmod.DataSourceManager)

        historical = historical or d2 is not None
        if not historical:
            vcds.ActiveEvents = 1
            vcds.EventsType = self.vcdsmod.EF_Always
        else:
            vcds.ActiveEvents = 0

        if d2 is not None:
            serie = vcds.NewDataSerie(symbol, timeframe, compression, d1, d2)
        else:
            serie = vcds.NewDataSerie(symbol, timeframe, compression, d1)

        data._setserie(serie)

        # processing of bars can continue
        data.OnNewDataSerieBar(serie, forcepush=historical)
        if historical:  # push the last bar
            q.put(None)  # Signal end of transmission
            dsconn = None
        else:
            dsconn = self.GetEvents(vcds, data)  # finally connect the events

        # pump events in this thread - call ping
        PumpEvents(timeout=data._getpingtmout, cb=data.ping)
        if dsconn is not None:
            del dsconn  # Docs recommend deleting the connection

        # Delete the series before coming out of the thread
        vcds.DeleteDataSource(serie)
        self.comtypes.CoUninitialize()  # Terminate com threading

    # Broker functions
    def _t_broker(self, broker):
"""Args::
    broker:"""
    broker:"""
        self.comtypes.CoInitialize()  # running in another thread
        trader = self.CreateObject(self.vcctmod.Trader)
        conn = self.GetEvents(trader, broker(trader))
        PumpEvents()
        del conn  # ensure events go away
        self.comtypes.CoUninitialize()
