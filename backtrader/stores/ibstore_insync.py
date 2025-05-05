#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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

# local import import ib_insync
import asyncio
import collections
import itertools
import logging
import random
import threading
import time
from copy import copy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Awaitable, Dict, Iterator, List, Optional, Union

from backtrader.stores.ibstore import IBStore
from backtrader.stores.ibstores import util as util
from backtrader.stores.ibstores.client import Client
from backtrader.stores.ibstores.contract import (
    Contract,
    ContractDescription,
    ContractDetails,
    TagValue,
)
from backtrader.stores.ibstores.objects import (
    AccountValue,
    BarDataList,
    DepthMktDataDescription,
    Execution,
    ExecutionFilter,
    Fill,
    HistogramData,
    HistoricalNews,
    HistoricalSchedule,
    NewsArticle,
    NewsBulletin,
    NewsProvider,
    NewsTick,
    OptionChain,
    OptionComputation,
    PnL,
    PnLSingle,
    PortfolioItem,
    Position,
    PriceIncrement,
    RealTimeBarList,
    ScanDataList,
    ScannerSubscription,
    SmartComponent,
    TradeLogEntry,
    WshEventData,
)
from backtrader.stores.ibstores.order import (
    BracketOrder,
    LimitOrder,
    Order,
    OrderState,
    OrderStatus,
    StopOrder,
    Trade,
)
from backtrader.stores.ibstores.ticker import Ticker
from backtrader.stores.ibstores.wrapper import Wrapper
from backtrader.utils import AutoDict
from backtrader.utils.py3 import queue
from eventkit import Event


class ErrorMsg(object):
    """ """

    def __init__(self, reqId, errorCode, errorString, advancedOrderRejectJson):
        """

        :param reqId:
        :param errorCode:
        :param errorString:
        :param advancedOrderRejectJson:

        """
        self.vars = vars()
        del self.vars["self"]
        self.reqId = reqId
        self.errorCode = errorCode
        self.errorString = errorString
        self.advancedOrderRejectJson = advancedOrderRejectJson

    def __str__(self):
        """ """
        return f"{self.vars}"


class OpenOrderMsg(object):
    """ """

    def __init__(self, orderId, contract, order, orderState):
        """

        :param orderId:
        :param contract:
        :param order:
        :param orderState:

        """
        self.vars = vars()
        del self.vars["self"]
        self.orderId = orderId
        self.contract = contract
        self.order = order
        self.orderState = orderState

    def __str__(self):
        """ """
        return f"{self.vars}"


class OrderStatusMsg(object):
    """ """

    def __init__(
        self,
        orderId,
        status,
        filled,
        remaining,
        avgFillPrice,
        permId,
        parentId,
        lastFillPrice,
        clientId,
        whyHeld,
        mktCapPrice,
    ):
        """

        :param orderId:
        :param status:
        :param filled:
        :param remaining:
        :param avgFillPrice:
        :param permId:
        :param parentId:
        :param lastFillPrice:
        :param clientId:
        :param whyHeld:
        :param mktCapPrice:

        """
        self.vars = vars()
        self.orderId = orderId
        self.status = status
        self.filled = filled
        self.remaining = remaining
        self.avgFillPrice = avgFillPrice
        self.permId = permId
        self.parentId = parentId
        self.lastFillPrice = lastFillPrice
        self.clientId = clientId
        self.whyHeld = whyHeld
        self.mktCapPrice = mktCapPrice

    def __str__(self):
        """ """
        return f"{self.vars}"


class HistBar(object):
    """Set historicalBar object"""

    def __init__(self, reqId, bar):
        """

        :param reqId:
        :param bar:

        """
        self.vars = vars()
        self.reqId = reqId
        self.date = bar.date
        self.open = bar.open
        self.high = bar.high
        self.low = bar.low
        self.close = bar.close
        self.volume = bar.volume
        self.wap = bar.wap
        self.count = bar.barCount

    def __str__(self):
        """ """
        return f"{self.vars}"


class HistTick(object):
    """Set historicalTick object: 'MIDPOINT', 'BID_ASK', 'TRADES'"""

    def __init__(self, tick, dataType):
        """

        :param tick:
        :param dataType:

        """
        self.vars = vars()
        self.date = datetime.utcfromtimestamp(tick.time)
        self.tickType = tick.tickType if hasattr(tick, "tickType") else int(0)
        self.dataType = dataType
        if dataType == "RT_TICK_MIDPOINT":
            self.price = tick.price
        elif dataType == "RT_TICK_LAST":
            self.price = tick.price
            self.size = float(tick.size)
            self.unreported = tick.tickAttribLast.unreported
            self.pastlimit = tick.tickAttribLast.pastLimit
        elif dataType == "RT_TICK_BID_ASK":
            self.bidPrice = tick.priceBid
            self.askPrice = tick.priceAsk
            self.bidSize = float(tick.sizeBid)
            self.askSize = float(tick.sizeAsk)

        # self.exchange = tick.exchange
        # self.specialconditions = tick.tickAttribLast.specialConditions

    def __str__(self):
        """ """
        return f"{self.vars}"


class RTTickLast(object):
    """Set realtimeTick object: 'TRADES'"""

    def __init__(
            self,
            tickType,
            time,
            price,
            size,
            tickAtrribLast,
            exchange,
            specialConditions):
        """

        :param tickType:
        :param time:
        :param price:
        :param size:
        :param tickAtrribLast:
        :param exchange:
        :param specialConditions:

        """
        self.vars = vars()
        self.dataType = "RT_TICK_LAST"
        self.datetime = datetime.utcfromtimestamp(time)
        # self.tickType = TickTypeEnum.to_str(tickType)
        self.tickType = tickType
        self.price = price
        self.size = float(size)
        self.pastlimit = tickAtrribLast.pastLimit
        self.unreported = tickAtrribLast.unreported
        # self.exchange = exchange
        # self.specialConditions = specialConditions

    def __str__(self):
        """ """
        return f"{self.vars}"


class RTTickBidAsk(object):
    """Set realtimeTick object: 'MIDPOINT', 'BID_ASK', 'TRADES'"""

    def __init__(
            self,
            time,
            bidPrice,
            askPrice,
            bidSize,
            askSize,
            tickAttribBidAsk):
        """

        :param time:
        :param bidPrice:
        :param askPrice:
        :param bidSize:
        :param askSize:
        :param tickAttribBidAsk:

        """
        self.vars = vars()
        self.dataType = "RT_TICK_BID_ASK"
        self.datetime = datetime.utcfromtimestamp(time)
        self.bidPrice = bidPrice
        self.askPrice = askPrice
        self.bidSize = float(bidSize)
        self.askSize = float(askSize)
        self.bidPastLow = tickAttribBidAsk.bidPastLow
        self.askPastHigh = tickAttribBidAsk.askPastHigh

    def __str__(self):
        """ """
        return f"{self.vars}"


class RTTickMidPoint(object):
    """Set realtimeTick object: 'MIDPOINT'"""

    def __init__(self, time, midPoint):
        """

        :param time:
        :param midPoint:

        """
        self.vars = vars()
        self.dataType = "RT_TICK_MIDPOINT"
        self.datetime = datetime.utcfromtimestamp(time)
        self.midPoint = midPoint

    def __str__(self):
        """ """
        return f"{self.vars}"


class IBStoreInsync(IBStore):
    """ """
    # Set a base for the data requests (historical/realtime) to distinguish the
    # id in the error notifications from orders, where the basis (usually
    # starting at 1) is set by TWS
    REQIDBASE = 0x01000000

    BrokerCls = None  # broker class will autoregister
    DataCls = None  # data class will auto register

    params = (
        ("host", "127.0.0.1"),
        ("port", 7496),
        ("clientId", None),  # None generates a random clientid 1 -> 2^16
        ("notifyall", False),
        ("_debug", False),
        ("reconnect", 3),  # -1 forever, 0 No, > 0 number of retries
        ("timeout", 3.0),  # timeout between reconnections
        ("timeoffset", True),  # Use offset to server for timestamps if needed
        ("timerefresh", 60.0),  # How often to refresh the timeoffset
        ("indcash", True),  # Treat IND codes as CASH elements
        ("runmode", None),
    )

    events = (
        "connectedEvent",
        "disconnectedEvent",
        "updateEvent",
        "pendingTickersEvent",
        "barUpdateEvent",
        "newOrderEvent",
        "orderModifyEvent",
        "cancelOrderEvent",
        "openOrderEvent",
        "orderStatusEvent",
        "execDetailsEvent",
        "commissionReportEvent",
        "updatePortfolioEvent",
        "positionEvent",
        "accountValueEvent",
        "accountSummaryEvent",
        "pnlEvent",
        "pnlSingleEvent",
        "scannerDataEvent",
        "tickNewsEvent",
        "newsBulletinEvent",
        "wshMetaEvent",
        "wshEvent",
        "errorEvent",
        "timeoutEvent",
    )

    RequestTimeout: float = 0
    RaiseRequestErrors: bool = False
    MaxSyncedSubAccounts: int = 50
    TimezoneTWS: str = ""

    @classmethod
    def adddata(cls, *args, **kwargs):
        """Returns ``DataCls`` with args, kwargs

        :param *args:
        :param **kwargs:

        """
        return super().getdata(*args, **kwargs)

    def getbroker(self):
        """Returns broker with *args, **kwargs from registered ``BrokerCls""" """""
        return super().getbroker()

    def __init__(self):
        """ """
        super(IBStore, self).__init__()

        self.runmode = self.p.runmode
        # Account list received
        self._event_accdownload = threading.Event()

        self.dontreconnect = False  # for non-recoverable connect errors
        self._allowtrade = False

        self._env = None  # reference to cerebro for general notifications
        self.broker = None  # broker instance
        self.datas = list()  # datas that have registered over start
        self.ccount = 0  # requests to start (from cerebro or datas)

        self._lock_tmoffset = threading.Lock()
        self.tmoffset = timedelta()  # to control time difference with server

        # Structures to hold datas requests
        self.qs = collections.OrderedDict()  # key: tickerId -> queues
        self.ts = collections.OrderedDict()  # key: queue -> tickerId
        self.iscash = dict()  # tickerIds from cash products (for ex: EUR.JPY)

        self.histexreq = dict()  # holds segmented historical requests
        self.histfmt = dict()  # holds datetimeformat for request
        self.histsend = dict()  # holds sessionend (data time) for request
        self.histtz = dict()  # holds sessionend (data time) for request

        self.acc_cash = AutoDict()  # current total cash per account
        self.acc_value = AutoDict()  # current total value per account
        self.acc_upds = AutoDict()  # current account valueinfos per account
        self.acc_margin = AutoDict()  # current total margin per account
        self.acc_validcash = AutoDict()  # current total valid cash per account

        self.port_update = False  # indicate whether to signal to broker

        self.positions = collections.defaultdict(Position)  # actual positions

        self._tickerId = itertools.count(self.REQIDBASE)  # unique tickerIds
        self.orderId = None  # next possible orderId (will be itertools.count)

        self.cdetails = collections.defaultdict(list)  # hold cdetails requests

        self.managed_accounts = list()  # received via managedAccounts

        self.notifs = queue.Queue()  # store notifications for cerebro

        # Use the provided clientId or a random one
        if self.p.clientId is None:
            self.clientId = random.randint(1, pow(2, 16) - 1)
        else:
            self.clientId = self.p.clientId

        # ibpy connection object
        self._createEvents()
        self.accountValueEvent += self.onUpdateAccountValue
        self.positionEvent += self.onUpdatePosition

        self.wrapper = Wrapper(self)
        self.client = Client(self.wrapper)
        self.errorEvent += self._onError
        self.client.apiEnd += self.disconnectedEvent
        self._logger = logging.getLogger("ib_insync.ib")
        self.enableLog(level=logging.WARNING)

        self.connect(
            host=self.p.host,
            port=self.p.port,
            clientId=self.clientId)

        count = 1
        while not self.isConnected():
            print(f"not connect ~~ ({count})")
            time.sleep(1)
            count += 1

        self._debug = self.p._debug
        # register a printall method if requested
        if self.p._debug or self.p.notifyall:
            pass
            # self.ibi.registerAll(self.watcher)

        # This utility key function transforms a barsize into a:
        #   (Timeframe, Compression) tuple which can be sorted

        def keyfn(x):
            """

            : param x:

            """
            n, t = x.split()
            tf, comp = self._sizes[t]
            return (tf, int(n) * comp)

        # This utility key function transforms a duration into a:
        #   (Timeframe, Compression) tuple which can be sorted
        def key2fn(x):
            """

            : param x:

            """
            n, d = x.split()
            tf = self._dur2tf[d]
            return (tf, int(n))

        # Generate a table of reverse durations
        self.revdur = collections.defaultdict(list)
        # The table (dict) is a ONE to MANY relation of
        #   duration -> barsizes
        # Here it is reversed to get a ONE to MANY relation of
        #   barsize -> durations
        for duration, barsizes in self._durations.items():
            for barsize in barsizes:
                self.revdur[keyfn(barsize)].append(duration)

        # Once managed, sort the durations according to real duration and not
        # to the text form using the utility key above
        for barsize in self.revdur:
            self.revdur[barsize].sort(key=key2fn)

    def nextOrderId(self) -> int:
        """

        : rtype: int

        """
        return self.client.getReqId()

    def start(self, data=None, broker=None):
        """

        : param data: (Default value=None)
        : param broker: (Default value=None)

        """
        self.reconnect(fromstart=True)  # reconnect should be an invariant

        # Datas require some processing to kickstart data reception
        if data is not None:
            self._env = data._env
            # For datas simulate a queue with None to kickstart co
            self.datas.append(data)

            # if connection fails, get a fake registration that will force the
            # datas to try to reconnect or else bail out
            return self.getTickerQueue(start=True)

        elif broker is not None:
            self.broker = broker

    def reconnect(self, fromstart=False, resub=False):
        """

        : param fromstart: (Default value=False)
        : param resub: (Default value=False)

        """
        # This method must be an invariant in that it can be called several
        # times from the same source and must be consistent. An exampler would
        # be 5 datas which are being received simultaneously and all request a
        # reconnect

        # Policy:
        #  - if dontreconnect has been set, no option to connect is possible
        #  - check connection and use the absence of isConnected as signal of
        #    first ever connection (add 1 to retries too)
        #  - Calculate the retries (forever or not)
        #  - Try to connct
        #  - If achieved and fromstart is false, the datas will be
        #    re-kickstarted to recreate the subscription
        firstconnect = False
        try:
            if self.client.isReady():
                if resub:
                    self.startdatas()
                return True  # nothing to do
        except AttributeError:
            # Not connected, several __getattr__ indirections to
            # self.ibi.sender.client.isConnected
            firstconnect = True

        if self.dontreconnect:
            return False

        # This is only invoked from the main thread by datas and therefore no
        # lock is needed to control synchronicity to it
        retries = self.p.reconnect
        if retries >= 0:
            retries += firstconnect

        while retries < 0 or retries:
            if not firstconnect:
                time.sleep(self.p.timeout)

            firstconnect = False

            if self.ibi.connect():
                if not fromstart or resub:
                    self.startdatas()
                return True  # connection successful

            if retries > 0:
                retries -= 1

        self.dontreconnect = True
        return False  # connection/reconnection failed

    def connectionClosed(self):
        """ """
        # Sometmes this comes without 1300/502 or any other and will not be
        # seen in error hence the need to manage the situation independently
        if self.connected():
            self.conn.disconnect()
            self.stopdatas()

    def accountDownloadEnd(self, accountName):
        """

        : param accountName:

        """
        # Signals the end of an account update
        # the event indicates it's over. It's only false once, and can be used
        # to find out if it has at least been downloaded once
        self._event_accdownload.set()
        if False:
            if self.port_update:
                self.broker.push_portupdate()

                self.port_update = False

    def contractDetailsEnd(self, reqId):
        """Signal end of contractdetails

        : param reqId:

        """
        # self.cancelQueue(self.qs[reqId], True)

    def contractDetails(self, reqId, contractDetails):
        """Receive answer and pass it to the queue

        : param reqId:
        : param contractDetails:

        """
        # self.qs[reqId].put(contractDetails)

    def onUpdatebar(self, bars, hasNewBar):
        """Receives x seconds Real Time Bars(at the time of writing only 5
        seconds are supported)

        Not valid for cash markets

        : param bars:
        : param hasNewBar:

        """
        # Get a naive localtime object
        # msg.time = datetime.utcfromtimestamp(float(msg.time))
        # self.qs[msg.reqId].put(msg)
        # curtime = bars[0].date
        print(f"updatebar tickId:{bars.reqId} size:{len(bars)}")

    def getposition(self, data=None, clone=False):
        """

        : param data: (Default value=None)
        : param clone: (Default value=False)

        """
        # Lock access to the position dicts. This is called from main thread
        # and updates could be happening in the background

        position = self.positions.get(data.contract.symbol)
        if position:
            return copy(position) if clone else position

        return None

    def historicalTicks(self, reqId, tick, type):
        """

        : param reqId:
        : param tick:
        : param type:

        """
        mytick = HistTick(tick, type)
        tickerId = reqId
        self.qs[tickerId].put(mytick)

    def historicalTicksEnd(self, reqId):
        """

        : param reqId:

        """
        tickerId = reqId
        q = self.qs[tickerId]
        self.cancelTickByTickData(q)

    def tickByTickBidAsk(
            self,
            reqId,
            time,
            bidPrice,
            askPrice,
            bidSize,
            askSize,
            tickAttribBidAsk):
        """

        : param reqId:
        : param time:
        : param bidPrice:
        : param askPrice:
        : param bidSize:
        : param askSize:
        : param tickAttribBidAsk:

        """
        tickerId = reqId
        tick = RTTickBidAsk(
            time, bidPrice, askPrice, bidSize, askSize, tickAttribBidAsk
        )
        self.qs[tickerId].put(tick)

    def tickByTickAllLast(
        self,
        reqId,
        tickType,
        time,
        price,
        size,
        tickAtrribLast,
        exchange,
        specialConditions,
    ):
        """

        : param reqId:
        : param tickType:
        : param time:
        : param price:
        : param size:
        : param tickAtrribLast:
        : param exchange:
        : param specialConditions:

        """
        tickerId = reqId
        tick = RTTickLast(
            tickType,
            time,
            price,
            size,
            tickAtrribLast,
            exchange,
            specialConditions)
        self.qs[tickerId].put(tick)

    def tickByTickMidPoint(self, reqId, time, midPoint):
        """

        : param reqId:
        : param time:
        : param midPoint:

        """
        tickerId = reqId
        tick = RTTickMidPoint(time, time, midPoint)
        self.qs[tickerId].put(tick)

    def startdatas(self):
        """ """
        # kickstrat datas, not returning until all of them have been done
        for data in self.datas:
            data.reqdata()

    def stopdatas(self):
        """ """
        # stop subs and force datas out of the loop (in LIFO order)
        qs = list(self.qs.values())
        ts = list()
        datacount = 0
        for data in self.datas:
            datacount += 1
            t = threading.Thread(
                name="startdatas" + str(datacount), target=data.canceldata
            )
            t.start()
            ts.append(t)

        for t in ts:
            t.join()

        for q in reversed(qs):  # datamaster the last one to get a None
            q.put(None)

    def error(
            self,
            reqId: int,
            errorCode: int,
            errorString: str,
            advancedOrderRejectJson: str):
        """

        : param reqId:
        : type reqId: int
        : param errorCode:
        : type errorCode: int
        : param errorString:
        : type errorString: str
        : param advancedOrderRejectJson:
        : type advancedOrderRejectJson: str

        """
        # 100-199 Order/Data/Historical related
        # 200-203 tickerId and Order Related
        # 300-399 A mix of things: orders, connectivity, tickers, misc errors
        # 400-449 Seem order related again
        # 500-531 Connectivity/Communication Errors
        # 10000-100027 Mix of special orders/routing
        # 1100-1102 TWS connectivy to the outside
        # 1300- Socket dropped in client-TWS communication
        # 2100-2110 Informative about Data Farm status (id=-1)

        # All errors are logged to the environment (cerebro), because many
        # errors in Interactive Brokers are actually informational and many may
        # actually be of interest to the user
        msg = ErrorMsg(reqId, errorCode, errorString, advancedOrderRejectJson)
        if msg.reqId > 0:
            print(f"Error WY: {msg}")
        else:
            print(f"{msg}")

        if msg.reqId == -1 and msg.errorCode == 502:
            print(msg.errorString)
        if not self.p.notifyall:
            self.notifs.put(
                (msg, tuple(
                    vars(msg).values()), dict(
                    vars(msg).items())))

        # Manage those events which have to do with connection
        if msg.errorCode is None:
            # Usually received as an error in connection of just before disconn
            pass
        elif msg.errorCode in [200, 203, 162, 320, 321, 322]:
            # cdetails 200 security not found, notify over right queue
            # cdetails 203 security not allowed for acct
            try:
                q = self.qs[msg.reqId]
            except KeyError:
                pass  # should not happend but it can
            else:
                self.cancelQueue(q, True)

        elif msg.errorCode in [354, 420]:
            # 354 no subscription, 420 no real-time bar for contract
            # the calling data to let the data know ... it cannot resub
            try:
                q = self.qs[msg.reqId]
            except KeyError:
                pass  # should not happend but it can
            else:
                q.put(-msg.errorCode)
                self.cancelQueue(q)

        elif msg.errorCode == 10225:
            # 10225-Bust event occurred, current subscription is deactivated.
            # Please resubscribe real-time bars immediately.
            try:
                q = self.qs[msg.reqId]
            except KeyError:
                pass  # should not happend but it can
            else:
                q.put(-msg.errorCode)

        elif msg.errorCode == 326:  # not recoverable, clientId in use
            self.dontreconnect = True
            self.conn.disconnect()
            self.stopdatas()

        elif msg.errorCode == 502:
            # Cannot connect to TWS: port, config not open, tws off (504 then)
            self.conn.disconnect()
            self.stopdatas()

        elif msg.errorCode == 504:  # Not Connected for data op
            # Once for each data
            # pass  # don't need to manage it

            # Connection lost - Notify ... datas will wait on the queue
            # with no messages arriving
            for q in self.ts:  # key: queue -> ticker
                q.put(-msg.errorCode)

        elif msg.errorCode == 1300:
            # TWS has been closed. The port for a new connection is there
            # newport = int(msg.errorMsg.split('-')[-1])  # bla bla bla -7496
            self.conn.disconnect()
            self.stopdatas()

        elif msg.errorCode == 1100:
            # Connection lost - Notify ... datas will wait on the queue
            # with no messages arriving
            for q in self.ts:  # key: queue -> ticker
                q.put(-msg.errorCode)

        elif msg.errorCode == 1101:
            # Connection restored and tickerIds are gone
            for q in self.ts:  # key: queue -> ticker
                q.put(-msg.errorCode)

        elif msg.errorCode == 1102:
            # Connection restored and tickerIds maintained
            for q in self.ts:  # key: queue -> ticker
                q.put(-msg.errorCode)

        elif msg.errorCode < 500:
            # Given the myriad of errorCodes, start by assuming is an order
            # error and if not, the checks there will let it go
            if msg.reqId < self.REQIDBASE:
                if self.broker is not None:
                    self.broker.push_ordererror(msg)
            else:
                # Cancel the queue if a "data" reqId error is given: sanity
                q = self.qs[msg.reqId]
                self.cancelQueue(q, True)

    def set_tradestatus(self, status=False):
        """

        : param status: (Default value=False)

        """
        self._allowtrade = status

    def get_tradestatus(self):
        """ """
        return self._allowtrade

    def makecontract(self) -> Contract:
        """returns an empty contract from the parameters without check

        : rtype: Contract

        """
        contract = Contract()
        return contract

    def openOrder(self, orderId, contract, order, orderState):
        """Receive the event ``openOrder`` events

        : param orderId:
        : param contract:
        : param order:
        : param orderState:

        """
        msg = OpenOrderMsg(orderId, contract, order, orderState)
        self.broker.push_orderstate(msg)

    def orderStatus(
        self,
        orderId: int,
        status: str,
        filled: float,
        remaining: float,
        avgFillPrice: float,
        permId: int,
        parentId: int,
        lastFillPrice: float,
        clientId: int,
        whyHeld: str,
        mktCapPrice: float = 0.0,
    ):
        """Receive the event ``orderStatus``

        : param orderId:
        : type orderId: int
        : param status:
        : type status: str
        : param filled:
        : type filled: float
        : param remaining:
        : type remaining: float
        : param avgFillPrice:
        : type avgFillPrice: float
        : param permId:
        : type permId: int
        : param parentId:
        : type parentId: int
        : param lastFillPrice:
        : type lastFillPrice: float
        : param clientId:
        : type clientId: int
        : param whyHeld:
        : type whyHeld: str
        : param mktCapPrice: (Default value=0.0)
        : type mktCapPrice: float

        """
        msg = OrderStatusMsg(
            orderId,
            status,
            filled,
            remaining,
            avgFillPrice,
            permId,
            parentId,
            lastFillPrice,
            clientId,
            whyHeld,
            mktCapPrice,
        )
        self.broker.push_orderstatus(msg)

    def execDetails(self, reqId, contract, execution):
        """Receive execDetails

        : param reqId:
        : param contract:
        : param execution:

        """
        execution.shares = float(execution.shares)
        execution.cumQty = float(execution.cumQty)
        self.broker.push_execution(execution)

    def validQueue(self, q):
        """Returns(bool) if a queue is still valid

        : param q:

        """
        return q in self.ts  # queue -> ticker

    def getContractDetails(self, contract, maxcount=None):
        """

        : param contract:
        : param maxcount: (Default value=None)

        """
        cds = list()
        cds = self.reqContractDetails(contract)

        if not cds or (maxcount and len(cds) > maxcount):
            err = "Ambiguous contract: none/multiple answers received"
            self.notifs.put((err, cds, {}))
            return None

        return cds

    def nextValidId(self, reqId):
        """

        : param reqId:

        """
        # Create a counter from the TWS notified value to apply to orders
        self.reqId = itertools.count(reqId)

    def getdatabycontract(self, contract):
        """Returns the data object for a contract

        : param contract:

        """
        for data in self.datas:
            if data.contract.symbol == contract.symbol:
                return data

        return None

    def onUpdatePosition(self, position):
        """

        : param position:

        """
        data = self.getdatabycontract(position.contract)
        # 连接时就会请求持仓信息，此时还没有data和broker，所以需要判断
        if data and self.broker:
            self.broker.positions[data]["price"] = position.avgCost / abs(
                position.position
            )
            self.broker.positions[data]["size"] = position.position
        self.positions[position.contract.symbol] = position

    def onUpdateAccountValue(self, key, value, currency, accountName):
        """

        : param key:
        : param value:
        : param currency:
        : param accountName:

        """
        # Lock access to the dicts where values are updated. This happens in a
        # sub-thread and could kick it at anytime
        self.acc_upds[accountName][key][currency] = value

        if key == "NetLiquidation":
            # NetLiquidationByCurrency and currency == 'BASE' is the same
            self.acc_value[accountName] = float(value)
        elif key == "CashBalance" and currency == "BASE":
            self.acc_cash[accountName] = float(value)
            margin = self.acc_margin.get(accountName, 0)
            self.acc_validcash[accountName] = float(value) - float(margin)
        elif key == "FullInitMarginReq":
            self.acc_margin[accountName] = float(value)
            cash = self.acc_cash.get(accountName, 0)
            self.acc_validcash[accountName] = float(cash) - float(value)

    def get_acc_values(self, account=None):
        """Returns all account value infos sent by TWS during regular updates
        Waits for at least 1 successful download

        If ``account`` is ``None`` then a dictionary with accounts as keys will
        be returned containing all accounts

        If account is specified or the system has only 1 account the dictionary
        corresponding to that account is returned

        : param account: (Default value=None)

        """
        if account is None:
            # wait for the managedAccount Messages
            # if self.connected():
            #     self._event_managed_accounts.wait()

            if not self.managed_accounts:
                return self.acc_upds.copy()

            elif len(self.managed_accounts) > 1:
                return self.acc_upds.copy()

            # Only 1 account, fall through to return only 1
            account = self.managed_accounts[0]

        try:
            return self.acc_upds[account].copy()
        except KeyError:
            pass

        return self.acc_upds.copy()

    def get_acc_value(self, account=None):
        """Returns the net liquidation value sent by TWS during regular updates
        Waits for at least 1 successful download

        If ``account`` is ``None`` then a dictionary with accounts as keys will
        be returned containing all accounts

        If account is specified or the system has only 1 account the dictionary
        corresponding to that account is returned

        : param account: (Default value=None)

        """
        if account is None:
            if not self.managed_accounts:
                return float()

            elif len(self.managed_accounts) > 1:
                return sum(self.acc_value.values())

            # Only 1 account, fall through to return only 1
            account = self.managed_accounts[0]

        try:
            return self.acc_value[account]
        except KeyError:
            pass

        return float()

    def get_acc_cash(self, account=None):
        """Returns the total cash value sent by TWS during regular updates
        Waits for at least 1 successful download

        If ``account`` is ``None`` then a dictionary with accounts as keys will
        be returned containing all accounts

        If account is specified or the system has only 1 account the dictionary
        corresponding to that account is returned

        : param account: (Default value=None)

        """
        # Wait for at least 1 account update download to have been finished
        # before the cash can be returned to the calling client
        # if self.connected():
        #   self._event_accdownload.wait()
        # Lock access to acc_cash to avoid an event intefering
        if account is None:
            if not self.managed_accounts:
                return 0

            elif len(self.managed_accounts) > 1:
                return sum(self.acc_cash.values())

            # Only 1 account, fall through to return only 1
            account = self.managed_accounts[0]

        try:
            return self.acc_cash[account]
        except KeyError:
            pass

    def get_acc_validcash(self, account=None):
        """Returns the total cash value sent by TWS during regular updates
        Waits for at least 1 successful download

        If ``account`` is ``None`` then a dictionary with accounts as keys will
        be returned containing all accounts

        If account is specified or the system has only 1 account the dictionary
        corresponding to that account is returned

        : param account: (Default value=None)

        """
        if account is None:
            if not self.managed_accounts:
                return 0

            elif len(self.managed_accounts) > 1:
                return sum(self.acc_validcash.values())

            # Only 1 account, fall through to return only 1
            account = self.managed_accounts[0]

        try:
            return self.acc_validcash[account]
        except KeyError:
            pass

    """
    ***************************************************************************
    ***************************************************************************
    ***************************************************************************
    ***************************************************************************
    ***************************************************************************
    """

    def _createEvents(self):
        """ """
        self.connectedEvent = Event("connectedEvent")
        self.disconnectedEvent = Event("disconnectedEvent")
        self.updateEvent = Event("updateEvent")
        self.pendingTickersEvent = Event("pendingTickersEvent")
        self.barUpdateEvent = Event("barUpdateEvent")
        self.newOrderEvent = Event("newOrderEvent")
        self.orderModifyEvent = Event("orderModifyEvent")
        self.cancelOrderEvent = Event("cancelOrderEvent")
        self.openOrderEvent = Event("openOrderEvent")
        self.orderStatusEvent = Event("orderStatusEvent")
        self.execDetailsEvent = Event("execDetailsEvent")
        self.commissionReportEvent = Event("commissionReportEvent")
        self.updatePortfolioEvent = Event("updatePortfolioEvent")
        self.positionEvent = Event("positionEvent")
        self.accountValueEvent = Event("accountValueEvent")
        self.accountSummaryEvent = Event("accountSummaryEvent")
        self.pnlEvent = Event("pnlEvent")
        self.pnlSingleEvent = Event("pnlSingleEvent")
        self.scannerDataEvent = Event("scannerDataEvent")
        self.tickNewsEvent = Event("tickNewsEvent")
        self.newsBulletinEvent = Event("newsBulletinEvent")
        self.wshMetaEvent = Event("wshMetaEvent")
        self.wshEvent = Event("wshEvent")
        self.errorEvent = Event("errorEvent")
        self.timeoutEvent = Event("timeoutEvent")

    def __del__(self):
        """ """
        self.disconnect()

    def __enter__(self):
        """ """
        return self

    def __exit__(self, *_exc):
        """

        : param * _exc:

        """
        self.disconnect()

    def __repr__(self):
        """ """
        conn = (
            f"connected to {self.client.host}:"
            f"{self.client.port} clientId={self.client.clientId}"
            if self.client.isConnected()
            else "not connected"
        )
        return f"<{self.__class__.__qualname__} {conn}>"

    def connect(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        clientId: int = 1,
        timeout: float = 4,
        readonly: bool = False,
        account: str = "",
        raiseSyncErrors: bool = False,
    ):
        """Connect to a running TWS or IB gateway application.
        After the connection is made the client is fully synchronized
        and ready to serve requests.

        This method is blocking.

        : param host: Host name or IP address. (Default value="127.0.0.1")
        : type host: str
        : param port: Port number. (Default value=7497)
        : type port: int
        : param clientId: ID number to use for this client; must be unique per
              connection. Setting clientId = 0 will automatically merge manual
              TWS trading with this client. (Default value=1)
        : type clientId: int
        : param timeout: If establishing the connection takes longer than
              ``timeout`` seconds then the ``asyncio.TimeoutError`` exception
              is raised. Set to 0 to disable timeout. (Default value=4)
        : type timeout: float
        : param readonly: Set to ``True`` when API is in read - only mode. (Default value=False)
        : type readonly: bool
        : param account: Main account to receive updates for . (Default value="")
        : type account: str
        : param raiseSyncErrors: When ``True`` this will cause an initial
              sync request error to raise a `ConnectionError``.
              When ``False`` the error will only be logged at error level. (Default value=False)
        : type raiseSyncErrors: bool

        """
        return self._run(
            self.connectAsync(
                host,
                port,
                clientId,
                timeout,
                readonly,
                account,
                raiseSyncErrors))

    def disconnect(self):
        """Disconnect from a TWS or IB gateway application.
        This will clear all session state.

        """
        if not self.client.isConnected():
            return
        stats = self.client.connectionStats()
        self._logger.info(
            f"Disconnecting from {self.client.host}:{self.client.port}, "
            f"{util.formatSI(stats.numBytesSent)}B sent "
            f"in {stats.numMsgSent} messages, "
            f"{util.formatSI(stats.numBytesRecv)}B received "
            f"in {stats.numMsgRecv} messages, "
            f"session time {util.formatSI(stats.duration)}s."
        )
        self.client.disconnect()
        self.disconnectedEvent.emit()

    def isConnected(self) -> bool:
        """Is there an API connection to TWS or IB gateway?

        : rtype: bool

        """
        return self.client.isReady()

    def enableLog(self, level=logging.DEBUG, logger=None):
        """Enables ib insync logging

        : param level: (Default value=logging.DEBUG)
        : param logger: (Default value=None)

        """
        util.logToConsole(level, logger)

    def _onError(self, reqId, errorCode, errorString, contract):
        """

        : param reqId:
        : param errorCode:
        : param errorString:
        : param contract:

        """
        if errorCode == 1102:
            # "Connectivity between IB and Trader Workstation has been
            # restored": Resubscribe to account summary.
            asyncio.ensure_future(self.reqAccountSummaryAsync())

    run = staticmethod(util.run)
    schedule = staticmethod(util.schedule)
    sleep = staticmethod(util.sleep)
    timeRange = staticmethod(util.timeRange)
    timeRangeAsync = staticmethod(util.timeRangeAsync)
    waitUntil = staticmethod(util.waitUntil)

    def _run(self, *awaitables: Awaitable):
        """

        : param * awaitables:
        : type *awaitables: Awaitable

        """
        return util.run(*awaitables, timeout=self.RequestTimeout)

    def waitOnUpdate(self, timeout: float = 0) -> bool:
        """Wait on any new update to arrive from the network.

        : param timeout: Maximum time in seconds to wait.
                If 0 then no timeout is used.
        .. note::
            A loop with ``waitOnUpdate`` should not be used to harvest
            tick data from tickers, since some ticks can go missing.
            This happens when multiple updates occur almost simultaneously;
            The ticks from the first update are then cleared.
            Use events instead to prevent this. (Default value=0)
        : type timeout: float
        : returns: ``True`` if not timed - out, ``False`` otherwise.
        : rtype: bool

        """
        if timeout:
            try:
                util.run(asyncio.wait_for(self.updateEvent, timeout))
            except asyncio.TimeoutError:
                return False
        else:
            util.run(self.updateEvent)
        return True

    def loopUntil(
            self,
            condition=None,
            timeout: float = 0) -> Iterator[object]:
        """Iterate until condition is met, with optional timeout in seconds.
        The yielded value is that of the condition or False when timed out.

        : param condition: Predicate function that is tested after every network
            update. (Default value=None)
        : param timeout: Maximum time in seconds to wait.
                If 0 then no timeout is used. (Default value=0)
        : type timeout: float
        : rtype: Iterator[object]

        """
        endTime = time.time() + timeout
        while True:
            test = condition and condition()
            if test:
                yield test
                return
            elif timeout and time.time() > endTime:
                yield False
                return
            else:
                yield test
            self.waitOnUpdate(endTime - time.time() if timeout else 0)

    def setTimeout(self, timeout: float = 60):
        """Set a timeout for receiving messages from TWS / IBG, emitting
        ``timeoutEvent`` if there is no incoming data for too long.

        The timeout fires once per connected session but can be set again
        after firing or after a reconnect.

        : param timeout: Timeout in seconds. (Default value=60)
        : type timeout: float

        """
        self.wrapper.setTimeout(timeout)

    def managedAccounts(self) -> List[str]:
        """List of account names.

        : rtype: List[str]

        """
        self.managed_accounts = self.wrapper.accounts.split(",")

        return list(self.wrapper.accounts)

    def accountValues(self, account: str = "") -> List[AccountValue]:
        """List of account values for the given account,
        or of all accounts if account is left blank.

        : param account: If specified, filter for this account name. (Default value="")
        : type account: str
        : rtype: List[AccountValue]

        """
        if account:
            return [
                v for v in self.wrapper.accountValues.values() if v.account == account
            ]
        else:
            return list(self.wrapper.accountValues.values())

    def accountSummary(self, account: str = "") -> List[AccountValue]:
        """List of account values for the given account,
        or of all accounts if account is left blank.

        This method is blocking on first run, non - blocking after that.

        : param account: If specified, filter for this account name. (Default value="")
        : type account: str
        : rtype: List[AccountValue]

        """
        return self._run(self.accountSummaryAsync(account))

    def portfolio(self, account: str = "") -> List[PortfolioItem]:
        """List of portfolio items for the given account,
        or of all retrieved portfolio items if account is left blank.

        : param account: If specified, filter for this account name. (Default value="")
        : type account: str
        : rtype: List[PortfolioItem]

        """
        if account:
            return list(self.wrapper.portfolio[account].values())
        else:
            return [v for d in self.wrapper.portfolio.values()
                    for v in d.values()]

    def positions(self, account: str = "") -> List[Position]:
        """List of positions for the given account,
        or of all accounts if account is left blank.

        : param account: If specified, filter for this account name. (Default value="")
        : type account: str
        : rtype: List[Position]

        """
        if account:
            return list(self.wrapper.positions[account].values())
        else:
            return [v for d in self.wrapper.positions.values()
                    for v in d.values()]

    def pnl(self, account="", modelCode="") -> List[PnL]:
        """List of subscribed: class: `.PnL` objects(profit and loss),
        optionally filtered by account and / or modelCode.

        The: class: `.PnL` objects are kept live updated.

        : param account: If specified, filter for this account name. (Default value="")
        : param modelCode: If specified, filter for this account model. (Default value="")
        : rtype: List[PnL]

        """
        return [
            v
            for v in self.wrapper.reqId2PnL.values()
            if (not account or v.account == account)
            and (not modelCode or v.modelCode == modelCode)
        ]

    def pnlSingle(
        self, account: str = "", modelCode: str = "", conId: int = 0
    ) -> List[PnLSingle]:
        """List of subscribed: class: `.PnLSingle` objects(profit and loss for
        single positions).

        The: class: `.PnLSingle` objects are kept live updated.

        : param account: If specified, filter for this account name. (Default value="")
        : type account: str
        : param modelCode: If specified, filter for this account model. (Default value="")
        : type modelCode: str
        : param conId: If specified, filter for this contract ID. (Default value=0)
        : type conId: int
        : rtype: List[PnLSingle]

        """
        return [
            v
            for v in self.wrapper.reqId2PnlSingle.values()
            if (not account or v.account == account)
            and (not modelCode or v.modelCode == modelCode)
            and (not conId or v.conId == conId)
        ]

    def trades(self) -> List[Trade]:
        """List of all order trades from this session.

        : rtype: List[Trade]

        """
        return list(self.wrapper.trades.values())

    def openTrades(self) -> List[Trade]:
        """List of all open order trades.

        : rtype: List[Trade]

        """
        return [
            v
            for v in self.wrapper.trades.values()
            if v.orderStatus.status not in OrderStatus.DoneStates
        ]

    def orders(self) -> List[Order]:
        """List of all orders from this session.

        : rtype: List[Order]

        """
        return list(trade.order for trade in self.wrapper.trades.values())

    def openOrders(self) -> List[Order]:
        """List of all open orders.

        : rtype: List[Order]

        """
        return [
            trade.order
            for trade in self.wrapper.trades.values()
            if trade.orderStatus.status not in OrderStatus.DoneStates
        ]

    def fills(self) -> List[Fill]:
        """List of all fills from this session.

        : rtype: List[Fill]

        """
        return list(self.wrapper.fills.values())

    def executions(self) -> List[Execution]:
        """List of all executions from this session.

        : rtype: List[Execution]

        """
        return list(fill.execution for fill in self.wrapper.fills.values())

    def ticker(self, contract: Contract) -> Optional[Ticker]:
        """Get ticker of the given contract. It must have been requested before
        with reqMktData with the same contract object. The ticker may not be
        ready yet if called directly after: meth: `.reqMktData`.

        : param contract: Contract to get ticker for .
        : type contract: Contract
        : rtype: Optional[Ticker]

        """
        return self.wrapper.tickers.get(id(contract))

    def tickers(self) -> List[Ticker]:
        """Get a list of all tickers.

        : rtype: List[Ticker]

        """
        return list(self.wrapper.tickers.values())

    def pendingTickers(self) -> List[Ticker]:
        """Get a list of all tickers that have pending ticks or domTicks.

        : rtype: List[Ticker]

        """
        return list(self.wrapper.pendingTickers)

    def realtimeBars(self) -> List[Union[BarDataList, RealTimeBarList]]:
        """Get a list of all live updated bars. These can be 5 second realtime
        bars or live updated historical bars.

        : rtype: List[Union[BarDataList, RealTimeBarList]]

        """
        return list(self.wrapper.reqId2Subscriber.values())

    def newsTicks(self) -> List[NewsTick]:
        """List of ticks with headline news.
        The article itself can be retrieved with: meth: `.reqNewsArticle`.

        : rtype: List[NewsTick]

        """
        return self.wrapper.newsTicks

    def newsBulletins(self) -> List[NewsBulletin]:
        """List of IB news bulletins.

        : rtype: List[NewsBulletin]

        """
        return list(self.wrapper.msgId2NewsBulletin.values())

    def reqTickers(
        self, *contracts: Contract, regulatorySnapshot: bool = False
    ) -> List[Ticker]:
        """Request and return a list of snapshot tickers.
        The list is returned when all tickers are ready.

        This method is blocking.

        : param * contracts:
        : type *contracts: Contract
        : param regulatorySnapshot: Request NBBO snapshots(may incur a fee). (Default value=False)
        : type regulatorySnapshot: bool
        : rtype: List[Ticker]

        """
        return self._run(
            self.reqTickersAsync(
                *contracts,
                regulatorySnapshot=regulatorySnapshot))

    def qualifyContracts(self, *contracts: Contract) -> List[Contract]:
        """Fully qualify the given contracts in -place. This will fill in
        the missing fields in the contract, especially the conId.

        Returns a list of contracts that have been successfully qualified.

        This method is blocking.

        : param * contracts:
        : type *contracts: Contract
        : rtype: List[Contract]

        """
        return self._run(self.qualifyContractsAsync(*contracts))

    def bracketOrder(
        self,
        action: str,
        totalQuantity: Decimal,
        lmtPrice: Decimal,
        takeProfitPrice: Decimal,
        stopLossPrice: Decimal,
        **kwargs,
    ) -> BracketOrder:
        """Create a limit order that is bracketed by a take - profit order and
        a stop - loss order. Submit the bracket like:

        .. code-block:: python

            for o in bracket:
                ib.placeOrder(contract, o)

        https: // interactivebrokers.github.io / tws - api / bracket_order.html

        : param action: 'BUY' or 'SELL'.
        : type action: str
        : param totalQuantity: Size of order.
        : type totalQuantity: Decimal
        : param lmtPrice:
        : type lmtPrice: Decimal
        : param takeProfitPrice: Limit price of profit order.
        : type takeProfitPrice: Decimal
        : param stopLossPrice: Stop price of loss order.
        : type stopLossPrice: Decimal
        : param ** kwargs:
        : rtype: BracketOrder

        """
        assert action in ("BUY", "SELL")
        reverseAction = "BUY" if action == "SELL" else "SELL"
        parent = LimitOrder(
            action,
            totalQuantity,
            lmtPrice,
            orderId=self.client.getReqId(),
            transmit=False,
            **kwargs,
        )
        takeProfit = LimitOrder(
            reverseAction,
            totalQuantity,
            takeProfitPrice,
            orderId=self.client.getReqId(),
            transmit=False,
            parentId=parent.orderId,
            **kwargs,
        )
        stopLoss = StopOrder(
            reverseAction,
            totalQuantity,
            stopLossPrice,
            orderId=self.client.getReqId(),
            transmit=True,
            parentId=parent.orderId,
            **kwargs,
        )
        return BracketOrder(parent, takeProfit, stopLoss)

    @staticmethod
    def oneCancelsAll(
            orders: List[Order],
            ocaGroup: str,
            ocaType: int) -> List[Order]:
        """Place the trades in the same One Cancels All(OCA) group.

        https: // interactivebrokers.github.io / tws - api / oca.html

        : param orders: The orders that are to be placed together.
        : type orders: List[Order]
        : param ocaGroup:
        : type ocaGroup: str
        : param ocaType:
        : type ocaType: int
        : rtype: List[Order]

        """
        for o in orders:
            o.ocaGroup = ocaGroup
            o.ocaType = ocaType
        return orders

    def whatIfOrder(self, contract: Contract, order: Order) -> OrderState:
        """Retrieve commission and margin impact without actually
        placing the order. The given order will not be modified in any way.

        This method is blocking.

        : param contract: Contract to test.
        : type contract: Contract
        : param order: Order to test.
        : type order: Order
        : rtype: OrderState

        """
        return self._run(self.whatIfOrderAsync(contract, order))

    def placeOrder(self, contract: Contract, order: Order) -> Trade:
        """Place a new order or modify an existing order.
        Returns a Trade that is kept live updated with
        status changes, fills, etc.

        : param contract: Contract to use for order.
        : type contract: Contract
        : param order: The order to be placed.
        : type order: Order
        : rtype: Trade

        """
        orderId = order.orderId or self.client.getReqId()
        self.client.placeOrder(orderId, contract, order)
        now = datetime.now(timezone.utc)
        key = self.wrapper.orderKey(
            self.wrapper.clientId, orderId, order.permId)
        trade = self.wrapper.trades.get(key)
        if trade:
            # this is a modification of an existing order
            assert trade.orderStatus.status not in OrderStatus.DoneStates
            logEntry = TradeLogEntry(now, trade.orderStatus.status, "Modify")
            trade.log.append(logEntry)
            self._logger.info(f"placeOrder: Modify order {trade}")
            trade.modifyEvent.emit(trade)
            self.orderModifyEvent.emit(trade)
        else:
            # this is a new order
            order.clientId = self.wrapper.clientId
            order.orderId = orderId
            orderStatus = OrderStatus(
                orderId=orderId, status=OrderStatus.PendingSubmit)
            logEntry = TradeLogEntry(now, orderStatus.status)
            trade = Trade(contract, order, orderStatus, [], [logEntry])
            self.wrapper.trades[key] = trade
            self._logger.info(f"placeOrder: New order {trade}")
            self.newOrderEvent.emit(trade)
        return trade

    def cancelOrder(
        self, order: Order, manualCancelOrderTime: str = ""
    ) -> Optional[Trade]:
        """Cancel the order and return the Trade it belongs to.

        : param order: The order to be canceled.
        : type order: Order
        : param manualCancelOrderTime: For audit trail. (Default value="")
        : type manualCancelOrderTime: str
        : rtype: Optional[Trade]

        """
        self.client.cancelOrder(order.orderId, manualCancelOrderTime)
        now = datetime.now(timezone.utc)
        key = self.wrapper.orderKey(
            order.clientId, order.orderId, order.permId)
        trade = self.wrapper.trades.get(key)
        if trade:
            if not trade.isDone():
                status = trade.orderStatus.status
                if (
                    status == OrderStatus.PendingSubmit
                    and not order.transmit
                    or status == OrderStatus.Inactive
                ):
                    newStatus = OrderStatus.Cancelled
                else:
                    newStatus = OrderStatus.PendingCancel
                logEntry = TradeLogEntry(now, newStatus)
                trade.log.append(logEntry)
                trade.orderStatus.status = newStatus
                self._logger.info(f"cancelOrder: {trade}")
                trade.cancelEvent.emit(trade)
                trade.statusEvent.emit(trade)
                self.cancelOrderEvent.emit(trade)
                self.orderStatusEvent.emit(trade)
                if newStatus == OrderStatus.Cancelled:
                    trade.cancelledEvent.emit(trade)
        else:
            self._logger.error(f"cancelOrder: Unknown orderId {order.orderId}")
        return trade

    def reqGlobalCancel(self):
        """Cancel all active trades including those placed by other
        clients or TWS / IB gateway.

        """
        self.client.reqGlobalCancel()
        self._logger.info("reqGlobalCancel")

    def reqCurrentTime(self) -> datetime:
        """Request TWS current time.

        This method is blocking.

        : rtype: datetime

        """
        return self._run(self.reqCurrentTimeAsync())

    def reqAccountUpdates(self, account: str = ""):
        """This is called at startup - no need to call again.

        Request account and portfolio values of the account
        and keep updated. Returns when both account values and portfolio
        are filled.

        This method is blocking.

        : param account: If specified, filter for this account name. (Default value="")
        : type account: str

        """
        self._run(self.reqAccountUpdatesAsync(account))

    def reqAccountUpdatesMulti(self, account: str = "", modelCode: str = ""):
        """It is recommended to use: meth: `.accountValues` instead.

        Request account values of multiple accounts and keep updated.

        This method is blocking.

        : param account: If specified, filter for this account name. (Default value="")
        : type account: str
        : param modelCode: If specified, filter for this account model. (Default value="")
        : type modelCode: str

        """
        self._run(self.reqAccountUpdatesMultiAsync(account, modelCode))

    def reqAccountSummary(self):
        """It is recommended to use: meth: `.accountSummary` instead.

        Request account values for all accounts and keep them updated.
        Returns when account summary is filled.

        This method is blocking.

        """
        self._run(self.reqAccountSummaryAsync())

    def reqAutoOpenOrders(self, autoBind: bool = True):
        """Bind manual TWS orders so that they can be managed from this client.
        The clientId must be 0 and the TWS API setting "Use negative numbers
        to bind automatic orders" must be checked.
        
        This request is automatically called when clientId=0.
        
        https://interactivebrokers.github.io/tws-api/open_orders.html
        https://interactivebrokers.github.io/tws-api/modifying_orders.html

        :param autoBind: Set binding on or off. (Default value = True)
        :type autoBind: bool

        """
        self.client.reqAutoOpenOrders(autoBind)

    def reqOpenOrders(self) -> List[Trade]:
        """Request and return a list of open orders.
        
        This method can give stale information where a new open order is not
        reported or an already filled or cancelled order is reported as open.
        It is recommended to use the more reliable and much faster
        :meth:`.openTrades` or :meth:`.openOrders` methods instead.
        
        This method is blocking.


        :rtype: List[Trade]

        """
        return self._run(self.reqOpenOrdersAsync())

    def reqAllOpenOrders(self) -> List[Trade]:
        """Request and return a list of all open orders over all clients.
        Note that the orders of other clients will not be kept in sync,
        use the master clientId mechanism instead to see other
        client's orders that are kept in sync.


        :rtype: List[Trade]

        """
        return self._run(self.reqAllOpenOrdersAsync())

    def reqCompletedOrders(self, apiOnly: bool) -> List[Trade]:
        """Request and return a list of completed trades.

        :param apiOnly: Request only API orders (not manually placed TWS orders).
        :type apiOnly: bool
        :rtype: List[Trade]

        """
        return self._run(self.reqCompletedOrdersAsync(apiOnly))

    def reqExecutions(
            self,
            execFilter: Optional[ExecutionFilter] = None) -> List[Fill]:
        """It is recommended to use :meth:`.fills`  or
        :meth:`.executions` instead.
        
        Request and return a list of fills.
        
        This method is blocking.

        :param execFilter: If specified, return executions that match the filter. (Default value = None)
        :type execFilter: Optional[ExecutionFilter]
        :rtype: List[Fill]

        """
        return self._run(self.reqExecutionsAsync(execFilter))

    def reqPositions(self) -> List[Position]:
        """It is recommended to use :meth:`.positions` instead.
        
        Request and return a list of positions for all accounts.
        
        This method is blocking.


        :rtype: List[Position]

        """
        return self._run(self.reqPositionsAsync())

    def reqPnL(self, account: str, modelCode: str = "") -> PnL:
        """Start a subscription for profit and loss events.
        
        Returns a :class:`.PnL` object that is kept live updated.
        The result can also be queried from :meth:`.pnl`.
        
        https://interactivebrokers.github.io/tws-api/pnl.html

        :param account: Subscribe to this account.
        :type account: str
        :param modelCode: If specified, filter for this account model. (Default value = "")
        :type modelCode: str
        :rtype: PnL

        """
        key = (account, modelCode)
        assert key not in self.wrapper.pnlKey2ReqId
        reqId = self.client.getReqId()
        self.wrapper.pnlKey2ReqId[key] = reqId
        pnl = PnL(account, modelCode)
        self.wrapper.reqId2PnL[reqId] = pnl
        self.client.reqPnL(reqId, account, modelCode)
        return pnl

    def cancelPnL(self, account, modelCode: str = ""):
        """Cancel PnL subscription.

        :param account: Cancel for this account.
        :param modelCode: If specified, cancel for this account model. (Default value = "")
        :type modelCode: str

        """
        key = (account, modelCode)
        reqId = self.wrapper.pnlKey2ReqId.pop(key, None)
        if reqId:
            self.client.cancelPnL(reqId)
            self.wrapper.reqId2PnL.pop(reqId, None)
        else:
            self._logger.error(
                "cancelPnL: No subscription for "
                f"account {account}, modelCode {modelCode}"
            )

    def reqPnLSingle(
            self,
            account: str,
            modelCode: str,
            conId: int) -> PnLSingle:
        """Start a subscription for profit and loss events for single positions.
        
        Returns a :class:`.PnLSingle` object that is kept live updated.
        The result can also be queried from :meth:`.pnlSingle`.
        
        https://interactivebrokers.github.io/tws-api/pnl.html

        :param account: Subscribe to this account.
        :type account: str
        :param modelCode: Filter for this account model.
        :type modelCode: str
        :param conId: Filter for this contract ID.
        :type conId: int
        :rtype: PnLSingle

        """
        key = (account, modelCode, conId)
        assert key not in self.wrapper.pnlSingleKey2ReqId
        reqId = self.client.getReqId()
        self.wrapper.pnlSingleKey2ReqId[key] = reqId
        pnlSingle = PnLSingle(account, modelCode, conId)
        self.wrapper.reqId2PnlSingle[reqId] = pnlSingle
        self.client.reqPnLSingle(reqId, account, modelCode, conId)
        return pnlSingle

    def cancelPnLSingle(self, account: str, modelCode: str, conId: int):
        """Cancel PnLSingle subscription for the given account, modelCode
        and conId.

        :param account: Cancel for this account name.
        :type account: str
        :param modelCode: Cancel for this account model.
        :type modelCode: str
        :param conId: Cancel for this contract ID.
        :type conId: int

        """
        key = (account, modelCode, conId)
        reqId = self.wrapper.pnlSingleKey2ReqId.pop(key, None)
        if reqId:
            self.client.cancelPnLSingle(reqId)
            self.wrapper.reqId2PnlSingle.pop(reqId, None)
        else:
            self._logger.error(
                "cancelPnLSingle: No subscription for "
                f"account {account}, modelCode {modelCode}, conId {conId}"
            )

    def reqContractDetails(self, contract: Contract) -> List[ContractDetails]:
        """Get a list of contract details that match the given contract.
        If the returned list is empty then the contract is not known;
        If the list has multiple values then the contract is ambiguous.
        
        The fully qualified contract is available in the the
        ContractDetails.contract attribute.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/contract_details.html

        :param contract: The contract to get details for.
        :type contract: Contract
        :rtype: List[ContractDetails]

        """
        return self._run(self.reqContractDetailsAsync(contract))

    def reqMatchingSymbols(self, pattern: str) -> List[ContractDescription]:
        """Request contract descriptions of contracts that match a pattern.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/matching_symbols.html

        :param pattern: The first few letters of the ticker symbol, or for
                longer strings a character sequence matching a word in
                the security name.
        :type pattern: str
        :rtype: List[ContractDescription]

        """
        return self._run(self.reqMatchingSymbolsAsync(pattern))

    def reqMarketRule(self, marketRuleId: int) -> PriceIncrement:
        """Request price increments rule.
        
        https://interactivebrokers.github.io/tws-api/minimum_increment.html

        :param marketRuleId: ID of market rule.
                The market rule IDs for a contract can be obtained
                via :meth:`.reqContractDetails` from
                :class:`.ContractDetails`.marketRuleIds,
                which contains a comma separated string of market rule IDs.
        :type marketRuleId: int
        :rtype: PriceIncrement

        """
        return self._run(self.reqMarketRuleAsync(marketRuleId))

    def reqRealTimeBars(
        self,
        contract: Contract,
        barSize: int,
        whatToShow: str,
        useRTH: bool,
        realTimeBarsOptions: List[TagValue] = [],
    ) -> RealTimeBarList:
        """Request realtime 5 second bars.
        
        https://interactivebrokers.github.io/tws-api/realtime_bars.html

        :param contract: Contract of interest.
        :type contract: Contract
        :param barSize: Must be 5.
        :type barSize: int
        :param whatToShow: Specifies the source for constructing bars.
                Can be 'TRADES', 'MIDPOINT', 'BID' or 'ASK'.
        :type whatToShow: str
        :param useRTH: If True then only show data from within Regular
                Trading Hours, if False then show all data.
        :type useRTH: bool
        :param realTimeBarsOptions: Unknown. (Default value = [])
        :type realTimeBarsOptions: List[TagValue]
        :rtype: RealTimeBarList

        """
        reqId = self.client.getReqId()
        bars = RealTimeBarList()
        bars.reqId = reqId
        bars.contract = contract
        bars.barSize = barSize
        bars.whatToShow = whatToShow
        bars.useRTH = useRTH
        bars.realTimeBarsOptions = realTimeBarsOptions or []
        self.wrapper.startSubscription(reqId, bars, contract)
        self.client.reqRealTimeBars(
            reqId, contract, barSize, whatToShow, useRTH, realTimeBarsOptions
        )
        return bars

    def cancelRealTimeBars(self, bars: RealTimeBarList):
        """Cancel the realtime bars subscription.

        :param bars: The bar list that was obtained from ``reqRealTimeBars``.
        :type bars: RealTimeBarList

        """
        self.client.cancelRealTimeBars(bars.reqId)
        self.wrapper.endSubscription(bars)

    def reqHistoricalData(
        self,
        contract: Contract,
        endDateTime: Union[datetime, date, str, None],
        durationStr: str,
        barSizeSetting: str,
        whatToShow: str,
        useRTH: bool,
        formatDate: int = 1,
        keepUpToDate: bool = False,
        chartOptions: List[TagValue] = [],
        timeout: float = 60,
    ) -> BarDataList:
        """Request historical bar data.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/historical_bars.html

        :param contract: Contract of interest.
        :type contract: Contract
        :param endDateTime: Can be set to '' to indicate the current time,
                or it can be given as a datetime.date or datetime.datetime,
                or it can be given as a string in 'yyyyMMdd HH:mm:ss' format.
                If no timezone is given then the TWS login timezone is used.
        :type endDateTime: Union[datetime, date, str, None]
        :param durationStr: Time span of all the bars. Examples:
                '60 S', '30 D', '13 W', '6 M', '10 Y'.
        :type durationStr: str
        :param barSizeSetting: Time period of one bar. Must be one of:
                '1 secs', '5 secs', '10 secs' 15 secs', '30 secs',
                '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
                '20 mins', '30 mins',
                '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
                '1 day', '1 week', '1 month'.
        :type barSizeSetting: str
        :param whatToShow: Specifies the source for constructing bars.
                Must be one of:
                'TRADES', 'MIDPOINT', 'BID', 'ASK', 'BID_ASK',
                'ADJUSTED_LAST', 'HISTORICAL_VOLATILITY',
                'OPTION_IMPLIED_VOLATILITY', 'REBATE_RATE', 'FEE_RATE',
                'YIELD_BID', 'YIELD_ASK', 'YIELD_BID_ASK', 'YIELD_LAST'.
                For 'SCHEDULE' use :meth:`.reqHistoricalSchedule`.
        :type whatToShow: str
        :param useRTH: If True then only show data from within Regular
                Trading Hours, if False then show all data.
        :type useRTH: bool
        :param formatDate: For an intraday request setting to 2 will cause
                the returned date fields to be timezone-aware
                datetime.datetime with UTC timezone, instead of local timezone
                as used by TWS. (Default value = 1)
        :type formatDate: int
        :param keepUpToDate: If True then a realtime subscription is started
                to keep the bars updated; ``endDateTime`` must be set
                empty ('') then. (Default value = False)
        :type keepUpToDate: bool
        :param chartOptions: Unknown. (Default value = [])
        :type chartOptions: List[TagValue]
        :param timeout: Timeout in seconds after which to cancel the request
                and return an empty bar series. Set to ``0`` to wait
                indefinitely. (Default value = 60)
        :type timeout: float
        :rtype: BarDataList

        """
        return self._run(
            self.reqHistoricalDataAsync(
                contract,
                endDateTime,
                durationStr,
                barSizeSetting,
                whatToShow,
                useRTH,
                formatDate,
                keepUpToDate,
                chartOptions,
                timeout,
            )
        )

    def cancelHistoricalData(self, bars: BarDataList):
        """Cancel the update subscription for the historical bars.

        :param bars: The bar list that was obtained from ``reqHistoricalData``
                with a keepUpToDate subscription.
        :type bars: BarDataList

        """
        self.client.cancelHistoricalData(bars.reqId)
        self.wrapper.endSubscription(bars)

    def reqHistoricalSchedule(
        self,
        contract: Contract,
        numDays: int,
        endDateTime: Union[datetime, date, str, None] = "",
        useRTH: bool = True,
    ) -> HistoricalSchedule:
        """Request historical schedule.
        
        This method is blocking.

        :param contract: Contract of interest.
        :type contract: Contract
        :param numDays: Number of days.
        :type numDays: int
        :param endDateTime: Can be set to '' to indicate the current time,
                or it can be given as a datetime.date or datetime.datetime,
                or it can be given as a string in 'yyyyMMdd HH:mm:ss' format.
                If no timezone is given then the TWS login timezone is used. (Default value = "")
        :type endDateTime: Union[datetime, date, str, None]
        :param useRTH: If True then show schedule for Regular Trading Hours,
                if False then for extended hours. (Default value = True)
        :type useRTH: bool
        :rtype: HistoricalSchedule

        """
        return self._run(
            self.reqHistoricalScheduleAsync(
                contract,
                numDays,
                endDateTime,
                useRTH))

    def reqHistoricalTicks(
        self,
        contract: Contract,
        startDateTime: Union[str, date],
        endDateTime: Union[str, date],
        numberOfTicks: int,
        whatToShow: str,
        useRth: bool,
        ignoreSize: bool = False,
        miscOptions: List[TagValue] = [],
    ) -> List:
        """Request historical ticks. The time resolution of the ticks
        is one second.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/historical_time_and_sales.html

        :param contract: Contract to query.
        :type contract: Contract
        :param startDateTime: Can be given as a datetime.date or
                datetime.datetime, or it can be given as a string in
                'yyyyMMdd HH:mm:ss' format.
                If no timezone is given then the TWS login timezone is used.
        :type startDateTime: Union[str, date]
        :param endDateTime: One of ``startDateTime`` or ``endDateTime`` can
                be given, the other must be blank.
        :type endDateTime: Union[str, date]
        :param numberOfTicks: Number of ticks to request (1000 max). The actual
                result can contain a bit more to accommodate all ticks in
                the latest second.
        :type numberOfTicks: int
        :param whatToShow: One of 'Bid_Ask', 'Midpoint' or 'Trades'.
        :type whatToShow: str
        :param useRth: 
        :type useRth: bool
        :param ignoreSize: Ignore bid/ask ticks that only update the size. (Default value = False)
        :type ignoreSize: bool
        :param miscOptions: Unknown. (Default value = [])
        :type miscOptions: List[TagValue]
        :rtype: List

        """
        return self._run(
            self.reqHistoricalTicksAsync(
                contract,
                startDateTime,
                endDateTime,
                numberOfTicks,
                whatToShow,
                useRth,
                ignoreSize,
                miscOptions,
            )
        )

    def reqMarketDataType(self, marketDataType: int):
        """Set the market data type used for :meth:`.reqMktData`.

        :param marketDataType: One of:
                * 1 = Live
                * 2 = Frozen
                * 3 = Delayed
                * 4 = Delayed frozen
        https://interactivebrokers.github.io/tws-api/market_data_type.html
        :type marketDataType: int

        """
        self.client.reqMarketDataType(marketDataType)

    def reqHeadTimeStamp(
            self,
            contract: Contract,
            whatToShow: str,
            useRTH: bool,
            formatDate: int = 1) -> datetime:
        """Get the datetime of earliest available historical data
        for the contract.

        :param contract: Contract of interest.
        :type contract: Contract
        :param whatToShow: 
        :type whatToShow: str
        :param useRTH: If True then only show data from within Regular
                Trading Hours, if False then show all data.
        :type useRTH: bool
        :param formatDate: If set to 2 then the result is returned as a
                timezone-aware datetime.datetime with UTC timezone. (Default value = 1)
        :type formatDate: int
        :rtype: datetime

        """
        return self._run(
            self.reqHeadTimeStampAsync(
                contract,
                whatToShow,
                useRTH,
                formatDate))

    def reqMktData(
        self,
        contract: Contract,
        genericTickList: str = "",
        snapshot: bool = False,
        regulatorySnapshot: bool = False,
        mktDataOptions: List[TagValue] = [],
    ) -> Ticker:
        """Subscribe to tick data or request a snapshot.
        Returns the Ticker that holds the market data. The ticker will
        initially be empty and gradually (after a couple of seconds)
        be filled.
        
        https://interactivebrokers.github.io/tws-api/md_request.html

        :param contract: Contract of interest.
        :type contract: Contract
        :param genericTickList: Comma separated IDs of desired
                generic ticks that will cause corresponding Ticker fields
                to be filled:
                =====  ================================================
                ID     Ticker fields
                =====  ================================================
                100    ``putVolume``, ``callVolume`` (for options)
                101    ``putOpenInterest``, ``callOpenInterest`` (for options)
                104    ``histVolatility`` (for options)
                105    ``avOptionVolume`` (for options)
                106    ``impliedVolatility`` (for options)
                162    ``indexFuturePremium``
                165    ``low13week``, ``high13week``, ``low26week``,
                       ``high26week``, ``low52week``, ``high52week``,
                       ``avVolume``
                221    ``markPrice``
                225    ``auctionVolume``, ``auctionPrice``,
                       ``auctionImbalance``
                233    ``last``, ``lastSize``, ``rtVolume``, ``rtTime``,
                       ``vwap`` (Time & Sales)
                236    ``shortableShares``
                258    ``fundamentalRatios`` (of type
                       :class:`ib_insync.objects.FundamentalRatios`)
                293    ``tradeCount``
                294    ``tradeRate``
                295    ``volumeRate``
                375    ``rtTradeVolume``
                411    ``rtHistVolatility``
                456    ``dividends`` (of type
                       :class:`ib_insync.objects.Dividends`)
                588    ``futuresOpenInterest``
                =====  ================================================ (Default value = "")
        :type genericTickList: str
        :param snapshot: If True then request a one-time snapshot, otherwise
                subscribe to a stream of realtime tick data. (Default value = False)
        :type snapshot: bool
        :param regulatorySnapshot: Request NBBO snapshot (may incur a fee). (Default value = False)
        :type regulatorySnapshot: bool
        :param mktDataOptions: Unknown (Default value = [])
        :type mktDataOptions: List[TagValue]
        :rtype: Ticker

        """
        reqId = self.client.getReqId()
        ticker = self.wrapper.startTicker(reqId, contract, "mktData")
        self.client.reqMktData(
            reqId,
            contract,
            genericTickList,
            snapshot,
            regulatorySnapshot,
            mktDataOptions,
        )
        return ticker

    def cancelMktData(self, contract: Contract):
        """Unsubscribe from realtime streaming tick data.

        :param contract: The exact contract object that was used to
                subscribe with.
        :type contract: Contract

        """
        ticker = self.ticker(contract)
        reqId = self.wrapper.endTicker(ticker, "mktData") if ticker else 0
        if reqId:
            self.client.cancelMktData(reqId)
        else:
            self._logger.error(
                f"cancelMktData: No reqId found for contract {contract}")

    def reqTickByTickData(
        self,
        contract: Contract,
        tickType: str,
        numberOfTicks: int = 0,
        ignoreSize: bool = False,
    ) -> Ticker:
        """Subscribe to tick-by-tick data and return the Ticker that
        holds the ticks in ticker.tickByTicks.
        
        https://interactivebrokers.github.io/tws-api/tick_data.html

        :param contract: Contract of interest.
        :type contract: Contract
        :param tickType: One of  'Last', 'AllLast', 'BidAsk' or 'MidPoint'.
        :type tickType: str
        :param numberOfTicks: Number of ticks or 0 for unlimited. (Default value = 0)
        :type numberOfTicks: int
        :param ignoreSize: Ignore bid/ask ticks that only update the size. (Default value = False)
        :type ignoreSize: bool
        :rtype: Ticker

        """
        reqId = self.client.getReqId()
        ticker = self.wrapper.startTicker(reqId, contract, tickType)
        self.client.reqTickByTickData(
            reqId, contract, tickType, numberOfTicks, ignoreSize
        )
        return ticker

    def cancelTickByTickData(self, contract: Contract, tickType: str):
        """Unsubscribe from tick-by-tick data

        :param contract: The exact contract object that was used to
                subscribe with.
        :type contract: Contract
        :param tickType: 
        :type tickType: str

        """
        ticker = self.ticker(contract)
        reqId = self.wrapper.endTicker(ticker, tickType) if ticker else 0
        if reqId:
            self.client.cancelTickByTickData(reqId)
        else:
            self._logger.error(
                f"cancelMktData: No reqId found for contract {contract}")

    def reqSmartComponents(self, bboExchange: str) -> List[SmartComponent]:
        """Obtain mapping from single letter codes to exchange names.
        
        Note: The exchanges must be open when using this request, otherwise an
        empty list is returned.

        :param bboExchange: 
        :type bboExchange: str
        :rtype: List[SmartComponent]

        """
        return self._run(self.reqSmartComponentsAsync(bboExchange))

    def reqMktDepthExchanges(self) -> List[DepthMktDataDescription]:
        """Get those exchanges that have have multiple market makers
        (and have ticks returned with marketMaker info).


        :rtype: List[DepthMktDataDescription]

        """
        return self._run(self.reqMktDepthExchangesAsync())

    def reqMktDepth(
        self,
        contract: Contract,
        numRows: int = 5,
        isSmartDepth: bool = False,
        mktDepthOptions=None,
    ) -> Ticker:
        """Subscribe to market depth data (a.k.a. DOM, L2 or order book).
        
        https://interactivebrokers.github.io/tws-api/market_depth.html

        :param contract: Contract of interest.
        :type contract: Contract
        :param numRows: Number of depth level on each side of the order book
                (5 max). (Default value = 5)
        :type numRows: int
        :param isSmartDepth: Consolidate the order book across exchanges. (Default value = False)
        :type isSmartDepth: bool
        :param mktDepthOptions: Unknown. (Default value = None)
        :returns: The Ticker that holds the market depth in ``ticker.domBids``
            and ``ticker.domAsks`` and the list of MktDepthData in
            ``ticker.domTicks``.
        :rtype: Ticker

        """
        reqId = self.client.getReqId()
        ticker = self.wrapper.startTicker(reqId, contract, "mktDepth")
        ticker.domBids.clear()
        ticker.domAsks.clear()
        self.client.reqMktDepth(
            reqId,
            contract,
            numRows,
            isSmartDepth,
            mktDepthOptions)
        return ticker

    def cancelMktDepth(self, contract: Contract, isSmartDepth=False):
        """Unsubscribe from market depth data.

        :param contract: The exact contract object that was used to
                subscribe with.
        :type contract: Contract
        :param isSmartDepth:  (Default value = False)

        """
        ticker = self.ticker(contract)
        reqId = self.wrapper.endTicker(ticker, "mktDepth") if ticker else 0
        if ticker and reqId:
            self.client.cancelMktDepth(reqId, isSmartDepth)
        else:
            self._logger.error(
                f"cancelMktDepth: No reqId found for contract {contract}"
            )

    def reqHistogramData(
        self, contract: Contract, useRTH: bool, period: str
    ) -> List[HistogramData]:
        """Request histogram data.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/histograms.html

        :param contract: Contract to query.
        :type contract: Contract
        :param useRTH: If True then only show data from within Regular
                Trading Hours, if False then show all data.
        :type useRTH: bool
        :param period: Period of which data is being requested, for example
                '3 days'.
        :type period: str
        :rtype: List[HistogramData]

        """
        return self._run(self.reqHistogramDataAsync(contract, useRTH, period))

    def reqFundamentalData(
        self,
        contract: Contract,
        reportType: str,
        fundamentalDataOptions: List[TagValue] = [],
    ) -> str:
        """Get fundamental data of a contract in XML format.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/fundamentals.html

        :param contract: Contract to query.
        :type contract: Contract
        :param reportType: * 'ReportsFinSummary': Financial summary
                * 'ReportsOwnership': Company's ownership
                * 'ReportSnapshot': Company's financial overview
                * 'ReportsFinStatements': Financial Statements
                * 'RESC': Analyst Estimates
                * 'CalendarReport': Company's calendar
        :type reportType: str
        :param fundamentalDataOptions: Unknown (Default value = [])
        :type fundamentalDataOptions: List[TagValue]
        :rtype: str

        """
        return self._run(
            self.reqFundamentalDataAsync(
                contract,
                reportType,
                fundamentalDataOptions))

    def reqScannerData(
        self,
        subscription: ScannerSubscription,
        scannerSubscriptionOptions: List[TagValue] = [],
        scannerSubscriptionFilterOptions: List[TagValue] = [],
    ) -> ScanDataList:
        """Do a blocking market scan by starting a subscription and canceling it
        after the initial list of results are in.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/market_scanners.html

        :param subscription: Basic filters.
        :type subscription: ScannerSubscription
        :param scannerSubscriptionOptions: Unknown. (Default value = [])
        :type scannerSubscriptionOptions: List[TagValue]
        :param scannerSubscriptionFilterOptions: Advanced generic filters. (Default value = [])
        :type scannerSubscriptionFilterOptions: List[TagValue]
        :rtype: ScanDataList

        """
        return self._run(
            self.reqScannerDataAsync(
                subscription,
                scannerSubscriptionOptions,
                scannerSubscriptionFilterOptions,
            )
        )

    def reqScannerSubscription(
        self,
        subscription: ScannerSubscription,
        scannerSubscriptionOptions: List[TagValue] = [],
        scannerSubscriptionFilterOptions: List[TagValue] = [],
    ) -> ScanDataList:
        """Subscribe to market scan data.
        
        https://interactivebrokers.github.io/tws-api/market_scanners.html

        :param subscription: What to scan for.
        :type subscription: ScannerSubscription
        :param scannerSubscriptionOptions: Unknown. (Default value = [])
        :type scannerSubscriptionOptions: List[TagValue]
        :param scannerSubscriptionFilterOptions: Unknown. (Default value = [])
        :type scannerSubscriptionFilterOptions: List[TagValue]
        :rtype: ScanDataList

        """
        reqId = self.client.getReqId()
        dataList = ScanDataList()
        dataList.reqId = reqId
        dataList.subscription = subscription
        dataList.scannerSubscriptionOptions = scannerSubscriptionOptions or []
        dataList.scannerSubscriptionFilterOptions = (
            scannerSubscriptionFilterOptions or []
        )
        self.wrapper.startSubscription(reqId, dataList)
        self.client.reqScannerSubscription(
            reqId,
            subscription,
            scannerSubscriptionOptions,
            scannerSubscriptionFilterOptions,
        )
        return dataList

    def cancelScannerSubscription(self, dataList: ScanDataList):
        """Cancel market data subscription.
        
        https://interactivebrokers.github.io/tws-api/market_scanners.html

        :param dataList: The scan data list that was obtained from
                :meth:`.reqScannerSubscription`.
        :type dataList: ScanDataList

        """
        self.client.cancelScannerSubscription(dataList.reqId)
        self.wrapper.endSubscription(dataList)

    def reqScannerParameters(self) -> str:
        """Requests an XML list of scanner parameters.
        
        This method is blocking.


        :rtype: str

        """
        return self._run(self.reqScannerParametersAsync())

    def calculateImpliedVolatility(
        self,
        contract: Contract,
        optionPrice: float,
        underPrice: float,
        implVolOptions: List[TagValue] = [],
    ) -> OptionComputation:
        """Calculate the volatility given the option price.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/option_computations.html

        :param contract: Option contract.
        :type contract: Contract
        :param optionPrice: Option price to use in calculation.
        :type optionPrice: float
        :param underPrice: Price of the underlier to use in calculation
        :type underPrice: float
        :param implVolOptions: Unknown (Default value = [])
        :type implVolOptions: List[TagValue]
        :rtype: OptionComputation

        """
        return self._run(
            self.calculateImpliedVolatilityAsync(
                contract, optionPrice, underPrice, implVolOptions
            )
        )

    def calculateOptionPrice(
        self,
        contract: Contract,
        volatility: float,
        underPrice: float,
        optPrcOptions: List[TagValue] = [],
    ) -> OptionComputation:
        """Calculate the option price given the volatility.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/option_computations.html

        :param contract: Option contract.
        :type contract: Contract
        :param volatility: Option volatility to use in calculation.
        :type volatility: float
        :param underPrice: Price of the underlier to use in calculation
        :type underPrice: float
        :param optPrcOptions:  (Default value = [])
        :type optPrcOptions: List[TagValue]
        :rtype: OptionComputation

        """
        return self._run(
            self.calculateOptionPriceAsync(
                contract, volatility, underPrice, optPrcOptions
            )
        )

    def reqSecDefOptParams(
        self,
        underlyingSymbol: str,
        futFopExchange: str,
        underlyingSecType: str,
        underlyingConId: int,
    ) -> List[OptionChain]:
        """Get the option chain.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/options.html

        :param underlyingSymbol: Symbol of underlier contract.
        :type underlyingSymbol: str
        :param futFopExchange: Exchange (only for ``FuturesOption``, otherwise
                leave blank).
        :type futFopExchange: str
        :param underlyingSecType: The type of the underlying security, like
                'STK' or 'FUT'.
        :type underlyingSecType: str
        :param underlyingConId: conId of the underlying contract.
        :type underlyingConId: int
        :rtype: List[OptionChain]

        """
        return self._run(
            self.reqSecDefOptParamsAsync(
                underlyingSymbol,
                futFopExchange,
                underlyingSecType,
                underlyingConId))

    def exerciseOptions(
        self,
        contract: Contract,
        exerciseAction: int,
        exerciseQuantity: int,
        account: str,
        override: int,
    ):
        """Exercise an options contract.
        
        https://interactivebrokers.github.io/tws-api/options.html

        :param contract: The option contract to be exercised.
        :type contract: Contract
        :param exerciseAction: * 1 = exercise the option
                * 2 = let the option lapse
        :type exerciseAction: int
        :param exerciseQuantity: Number of contracts to be exercised.
        :type exerciseQuantity: int
        :param account: Destination account.
        :type account: str
        :param override: * 0 = no override
                * 1 = override the system's natural action
        :type override: int

        """
        reqId = self.client.getReqId()
        self.client.exerciseOptions(
            reqId,
            contract,
            exerciseAction,
            exerciseQuantity,
            account,
            override)

    def reqNewsProviders(self) -> List[NewsProvider]:
        """Get a list of news providers.
        
        This method is blocking.


        :rtype: List[NewsProvider]

        """
        return self._run(self.reqNewsProvidersAsync())

    def reqNewsArticle(
            self,
            providerCode: str,
            articleId: str,
            newsArticleOptions: List[TagValue] = []) -> NewsArticle:
        """Get the body of a news article.
        
        This method is blocking.
        
        https://interactivebrokers.github.io/tws-api/news.html

        :param providerCode: Code indicating news provider, like 'BZ' or 'FLY'.
        :type providerCode: str
        :param articleId: ID of the specific article.
        :type articleId: str
        :param newsArticleOptions: Unknown. (Default value = [])
        :type newsArticleOptions: List[TagValue]
        :rtype: NewsArticle

        """
        return self._run(
            self.reqNewsArticleAsync(
                providerCode,
                articleId,
                newsArticleOptions))

    def reqHistoricalNews(
        self,
        conId: int,
        providerCodes: str,
        startDateTime: Union[str, date],
        endDateTime: Union[str, date],
        totalResults: int,
        historicalNewsOptions: List[TagValue] = [],
    ) -> HistoricalNews:
        """Get historical news headline.
        
        https://interactivebrokers.github.io/tws-api/news.html
        
        This method is blocking.

        :param conId: Search news articles for contract with this conId.
        :type conId: int
        :param providerCodes: A '+'-separated list of provider codes, like
                'BZ+FLY'.
        :type providerCodes: str
        :param startDateTime: The (exclusive) start of the date range.
                Can be given as a datetime.date or datetime.datetime,
                or it can be given as a string in 'yyyyMMdd HH:mm:ss' format.
                If no timezone is given then the TWS login timezone is used.
        :type startDateTime: Union[str, date]
        :param endDateTime: The (inclusive) end of the date range.
                Can be given as a datetime.date or datetime.datetime,
                or it can be given as a string in 'yyyyMMdd HH:mm:ss' format.
                If no timezone is given then the TWS login timezone is used.
        :type endDateTime: Union[str, date]
        :param totalResults: Maximum number of headlines to fetch (300 max).
        :type totalResults: int
        :param historicalNewsOptions: Unknown. (Default value = [])
        :type historicalNewsOptions: List[TagValue]
        :rtype: HistoricalNews

        """
        return self._run(
            self.reqHistoricalNewsAsync(
                conId,
                providerCodes,
                startDateTime,
                endDateTime,
                totalResults,
                historicalNewsOptions,
            )
        )

    def reqNewsBulletins(self, allMessages: bool):
        """Subscribe to IB news bulletins.
        
        https://interactivebrokers.github.io/tws-api/news.html

        :param allMessages: If True then fetch all messages for the day.
        :type allMessages: bool

        """
        self.client.reqNewsBulletins(allMessages)

    def cancelNewsBulletins(self):
        """Cancel subscription to IB news bulletins."""
        self.client.cancelNewsBulletins()

    def requestFA(self, faDataType: int):
        """Requests to change the FA configuration.
        
        This method is blocking.

        :param faDataType: * 1 = Groups: Offer traders a way to create a group of
                  accounts and apply a single allocation method to all
                  accounts in the group.
                * 2 = Profiles: Let you allocate shares on an
                  account-by-account basis using a predefined calculation
                  value.
                * 3 = Account Aliases: Let you easily identify the accounts
                  by meaningful names rather than account numbers.
        :type faDataType: int

        """
        return self._run(self.requestFAAsync(faDataType))

    def replaceFA(self, faDataType: int, xml: str):
        """Replaces Financial Advisor's settings.

        :param faDataType: See :meth:`.requestFA`.
        :type faDataType: int
        :param xml: The XML-formatted configuration string.
        :type xml: str

        """
        reqId = self.client.getReqId()
        self.client.replaceFA(reqId, faDataType, xml)

    def reqWshMetaData(self):
        """Request Wall Street Horizon metadata.
        
        https://interactivebrokers.github.io/tws-api/fundamentals.html


        """
        if self.wrapper.wshMetaReqId:
            self._logger.warning("reqWshMetaData already active")
        else:
            reqId = self.client.getReqId()
            self.wrapper.wshMetaReqId = reqId
            self.client.reqWshMetaData(reqId)

    def cancelWshMetaData(self):
        """Cancel WSH metadata."""
        reqId = self.wrapper.wshMetaReqId
        if not reqId:
            self._logger.warning("reqWshMetaData not active")
        else:
            self.client.cancelWshMetaData(reqId)
            self.wrapper.wshMetaReqId = 0

    def reqWshEventData(self, data: WshEventData):
        """Request Wall Street Horizon event data.
        
        :meth:`.reqWshMetaData` must have been called first before using this
        method.

        :param data: Filters for selecting the corporate event data.
        https://interactivebrokers.github.io/tws-api/wshe_filters.html
        :type data: WshEventData

        """
        if self.wrapper.wshEventReqId:
            self._logger.warning("reqWshEventData already active")
        else:
            reqId = self.client.getReqId()
            self.wrapper.wshEventReqId = reqId
            self.client.reqWshEventData(reqId, data)

    def cancelWshEventData(self):
        """Cancel active WHS event data."""
        reqId = self.wrapper.wshEventReqId
        if not reqId:
            self._logger.warning("reqWshEventData not active")
        else:
            self.client.cancelWshEventData(reqId)
            self.wrapper.wshEventReqId = 0

    def getWshMetaData(self) -> str:
        """Blocking convenience method that returns the WSH metadata (that is
        the available filters and event types) as a JSON string.
        
        Please note that a `Wall Street Horizon subscription
        <https://www.wallstreethorizon.com/interactive-brokers>`_
        is required.
        
        .. code-block:: python
        
            # Get the list of available filters and event types:
            meta = ib.getWshMetaData()
            print(meta)


        :rtype: str

        """
        return self._run(self.getWshMetaDataAsync())

    def getWshEventData(self, data: WshEventData) -> str:
        """Blocking convenience method that returns the WSH event data as
        a JSON string.
        :meth:`.getWshMetaData` must have been called first before using this
        method.
        
        Please note that a  `Wall Street Horizon subscription
        <https://www.wallstreethorizon.com/interactive-brokers>`_
        is required.
        
        .. code-block:: python
        
            # For IBM (with conId=8314) query the:
            #   - Earnings Dates (wshe_ed)
            #   - Board of Directors meetings (wshe_bod)
            data = WshEventData(
                filter = '''{
                  "country": "All",
                  "watchlist": ["8314"],
                  "limit_region": 10,
                  "limit": 10,
                  "wshe_ed": "true",
                  "wshe_bod": "true"
                }''')
            events = ib.getWshEventData(data)
            print(events)

        :param data: 
        :type data: WshEventData
        :rtype: str

        """
        return self._run(self.getWshEventDataAsync(data))

    def reqUserInfo(self) -> str:
        """Get the White Branding ID of the user.


        :rtype: str

        """
        return self._run(self.reqUserInfoAsync())

    # now entering the parallel async universe

    async def connectAsync(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        clientId: int = 1,
        timeout: Optional[float] = 4,
        readonly: bool = False,
        account: str = "",
        raiseSyncErrors: bool = False,
    ):
        """

        :param host:  (Default value = "127.0.0.1")
        :type host: str
        :param port:  (Default value = 7497)
        :type port: int
        :param clientId:  (Default value = 1)
        :type clientId: int
        :param timeout:  (Default value = 4)
        :type timeout: Optional[float]
        :param readonly:  (Default value = False)
        :type readonly: bool
        :param account:  (Default value = "")
        :type account: str
        :param raiseSyncErrors:  (Default value = False)
        :type raiseSyncErrors: bool

        """
        clientId = int(clientId)
        self.wrapper.clientId = clientId
        timeout = timeout or None
        try:
            # establish API connection
            await self.client.connectAsync(host, port, clientId, timeout)

            # autobind manual orders
            if clientId == 0:
                self.reqAutoOpenOrders(True)

            accounts = self.client.getAccounts()
            self.managed_accounts = accounts
            if not account and len(accounts) == 1:
                account = accounts[0]

            # prepare initializing requests
            reqs: Dict = {}  # name -> request
            reqs["positions"] = self.reqPositionsAsync()
            if not readonly:
                reqs["open orders"] = self.reqOpenOrdersAsync()
            if not readonly and self.client.serverVersion() >= 150:
                reqs["completed orders"] = self.reqCompletedOrdersAsync(False)
            if account:
                reqs["account updates"] = self.reqAccountUpdatesAsync(account)
            if len(accounts) <= self.MaxSyncedSubAccounts:
                for acc in accounts:
                    reqs[f"account updates for {acc}"] = (
                        self.reqAccountUpdatesMultiAsync(acc)
                    )

            # run initializing requests concurrently and log if any times out
            tasks = [asyncio.wait_for(req, timeout) for req in reqs.values()]
            errors = []
            resps = await asyncio.gather(*tasks, return_exceptions=True)
            for name, resp in zip(reqs, resps):
                if isinstance(resp, asyncio.TimeoutError):
                    msg = f"{name} request timed out"
                    errors.append(msg)
                    self._logger.error(msg)

            # the request for executions must come after all orders are in
            try:
                await asyncio.wait_for(self.reqExecutionsAsync(), timeout)
            except asyncio.TimeoutError:
                msg = "executions request timed out"
                errors.append(msg)
                self._logger.error(msg)

            if raiseSyncErrors and len(errors) > 0:
                raise ConnectionError(errors)

            # final check if socket is still ready
            if not self.client.isReady():
                raise ConnectionError(
                    "Socket connection broken while connecting")

            self._logger.info("Synchronization complete")
            self.connectedEvent.emit()
        except BaseException:
            self.disconnect()
            raise
        return self

    async def qualifyContractsAsync(self, *
                                    contracts: Contract) -> List[Contract]:
        """

        :param *contracts: 
        :type *contracts: Contract
        :rtype: List[Contract]

        """
        detailsLists = await asyncio.gather(
            *(self.reqContractDetailsAsync(c) for c in contracts)
        )
        result = []
        for contract, detailsList in zip(contracts, detailsLists):
            if not detailsList:
                self._logger.warning(f"Unknown contract: {contract}")
            elif len(detailsList) > 1:
                possibles = [details.contract for details in detailsList]
                self._logger.warning(
                    f"Ambiguous contract: {contract}, possibles are {possibles}")
            else:
                c = detailsList[0].contract
                assert c
                if contract.exchange == "SMART":
                    # overwriting 'SMART' exchange can create invalid contract
                    c.exchange = contract.exchange
                util.dataclassUpdate(contract, c)
                result.append(contract)
        return result

    async def reqTickersAsync(
        self, *contracts: Contract, regulatorySnapshot: bool = False
    ) -> List[Ticker]:
        """

        :param *contracts: 
        :type *contracts: Contract
        :param regulatorySnapshot:  (Default value = False)
        :type regulatorySnapshot: bool
        :rtype: List[Ticker]

        """
        futures = []
        tickers = []
        reqIds = []
        for contract in contracts:
            reqId = self.client.getReqId()
            reqIds.append(reqId)
            future = self.wrapper.startReq(reqId, contract)
            futures.append(future)
            ticker = self.wrapper.startTicker(reqId, contract, "snapshot")
            tickers.append(ticker)
            self.client.reqMktData(
                reqId, contract, "", True, regulatorySnapshot, [])
        await asyncio.gather(*futures)
        for ticker in tickers:
            self.wrapper.endTicker(ticker, "snapshot")
        return tickers

    def whatIfOrderAsync(
        self, contract: Contract, order: Order
    ) -> Awaitable[OrderState]:
        """

        :param contract: 
        :type contract: Contract
        :param order: 
        :type order: Order
        :rtype: Awaitable[OrderState]

        """
        whatIfOrder = copy.copy(order)
        whatIfOrder.whatIf = True
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId, contract)
        self.client.placeOrder(reqId, contract, whatIfOrder)
        return future

    def reqCurrentTimeAsync(self) -> Awaitable[datetime]:
        """


        :rtype: Awaitable[datetime]

        """
        future = self.wrapper.startReq("currentTime")
        self.client.reqCurrentTime()
        return future

    def reqAccountUpdatesAsync(self, account: str) -> Awaitable[None]:
        """

        :param account: 
        :type account: str
        :rtype: Awaitable[None]

        """
        future = self.wrapper.startReq("accountValues")
        self.client.reqAccountUpdates(True, account)
        return future

    def reqAccountUpdatesMultiAsync(
        self, account: str, modelCode: str = ""
    ) -> Awaitable[None]:
        """

        :param account: 
        :type account: str
        :param modelCode:  (Default value = "")
        :type modelCode: str
        :rtype: Awaitable[None]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId)
        self.client.reqAccountUpdatesMulti(reqId, account, modelCode, False)
        return future

    async def accountSummaryAsync(
            self, account: str = "") -> List[AccountValue]:
        """

        :param account:  (Default value = "")
        :type account: str
        :rtype: List[AccountValue]

        """
        if not self.wrapper.acctSummary:
            # loaded on demand since it takes ca. 250 ms
            await self.reqAccountSummaryAsync()
        if account:
            return [
                v for v in self.wrapper.acctSummary.values() if v.account == account
            ]
        else:
            return list(self.wrapper.acctSummary.values())

    def reqAccountSummaryAsync(self) -> Awaitable[None]:
        """


        :rtype: Awaitable[None]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId)
        tags = (
            "AccountType,NetLiquidation,TotalCashValue,SettledCash,"
            "AccruedCash,BuyingPower,EquityWithLoanValue,"
            "PreviousDayEquityWithLoanValue,GrossPositionValue,RegTEquity,"
            "RegTMargin,SMA,InitMarginReq,MaintMarginReq,AvailableFunds,"
            "ExcessLiquidity,Cushion,FullInitMarginReq,FullMaintMarginReq,"
            "FullAvailableFunds,FullExcessLiquidity,LookAheadNextChange,"
            "LookAheadInitMarginReq,LookAheadMaintMarginReq,"
            "LookAheadAvailableFunds,LookAheadExcessLiquidity,"
            "HighestSeverity,DayTradesRemaining,DayTradesRemainingT+1,"
            "DayTradesRemainingT+2,DayTradesRemainingT+3,"
            "DayTradesRemainingT+4,Leverage,$LEDGER:ALL"
        )
        self.client.reqAccountSummary(reqId, "All", tags)
        return future

    def reqOpenOrdersAsync(self) -> Awaitable[List[Trade]]:
        """


        :rtype: Awaitable[List[Trade]]

        """
        future = self.wrapper.startReq("openOrders")
        self.client.reqOpenOrders()
        return future

    def reqAllOpenOrdersAsync(self) -> Awaitable[List[Trade]]:
        """


        :rtype: Awaitable[List[Trade]]

        """
        future = self.wrapper.startReq("openOrders")
        self.client.reqAllOpenOrders()
        return future

    def reqCompletedOrdersAsync(self, apiOnly: bool) -> Awaitable[List[Trade]]:
        """

        :param apiOnly: 
        :type apiOnly: bool
        :rtype: Awaitable[List[Trade]]

        """
        future = self.wrapper.startReq("completedOrders")
        self.client.reqCompletedOrders(apiOnly)
        return future

    def reqExecutionsAsync(
        self, execFilter: Optional[ExecutionFilter] = None
    ) -> Awaitable[List[Fill]]:
        """

        :param execFilter:  (Default value = None)
        :type execFilter: Optional[ExecutionFilter]
        :rtype: Awaitable[List[Fill]]

        """
        execFilter = execFilter or ExecutionFilter()
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId)
        self.client.reqExecutions(reqId, execFilter)
        return future

    def reqPositionsAsync(self) -> Awaitable[List[Position]]:
        """


        :rtype: Awaitable[List[Position]]

        """
        future = self.wrapper.startReq("positions")
        self.client.reqPositions()
        return future

    def reqContractDetailsAsync(
        self, contract: Contract
    ) -> Awaitable[List[ContractDetails]]:
        """

        :param contract: 
        :type contract: Contract
        :rtype: Awaitable[List[ContractDetails]]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId, contract)
        self.client.reqContractDetails(reqId, contract)
        return future

    async def reqMatchingSymbolsAsync(
        self, pattern: str
    ) -> Optional[List[ContractDescription]]:
        """

        :param pattern: 
        :type pattern: str
        :rtype: Optional[List[ContractDescription]]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId)
        self.client.reqMatchingSymbols(reqId, pattern)
        try:
            await asyncio.wait_for(future, 4)
            return future.result()
        except asyncio.TimeoutError:
            self._logger.error("reqMatchingSymbolsAsync: Timeout")
            return None

    async def reqMarketRuleAsync(
        self, marketRuleId: int
    ) -> Optional[List[PriceIncrement]]:
        """

        :param marketRuleId: 
        :type marketRuleId: int
        :rtype: Optional[List[PriceIncrement]]

        """
        future = self.wrapper.startReq(f"marketRule-{marketRuleId}")
        try:
            self.client.reqMarketRule(marketRuleId)
            await asyncio.wait_for(future, 1)
            return future.result()
        except asyncio.TimeoutError:
            self._logger.error("reqMarketRuleAsync: Timeout")
            return None

    async def reqHistoricalDataAsync(
        self,
        contract: Contract,
        endDateTime: Union[datetime, date, str, None],
        durationStr: str,
        barSizeSetting: str,
        whatToShow: str,
        useRTH: bool,
        formatDate: int = 1,
        keepUpToDate: bool = False,
        chartOptions: List[TagValue] = [],
        timeout: float = 60,
    ) -> BarDataList:
        """

        :param contract: 
        :type contract: Contract
        :param endDateTime: 
        :type endDateTime: Union[datetime, date, str, None]
        :param durationStr: 
        :type durationStr: str
        :param barSizeSetting: 
        :type barSizeSetting: str
        :param whatToShow: 
        :type whatToShow: str
        :param useRTH: 
        :type useRTH: bool
        :param formatDate:  (Default value = 1)
        :type formatDate: int
        :param keepUpToDate:  (Default value = False)
        :type keepUpToDate: bool
        :param chartOptions:  (Default value = [])
        :type chartOptions: List[TagValue]
        :param timeout:  (Default value = 60)
        :type timeout: float
        :rtype: BarDataList

        """
        reqId = self.client.getReqId()
        bars = BarDataList()
        bars.reqId = reqId
        bars.contract = contract
        bars.endDateTime = endDateTime
        bars.durationStr = durationStr
        bars.barSizeSetting = barSizeSetting
        bars.whatToShow = whatToShow
        bars.useRTH = useRTH
        bars.formatDate = formatDate
        bars.keepUpToDate = keepUpToDate
        bars.chartOptions = chartOptions or []
        future = self.wrapper.startReq(reqId, contract, container=bars)
        if keepUpToDate:
            self.wrapper.startSubscription(reqId, bars, contract)
        end = util.formatIBDatetime(endDateTime)
        self.client.reqHistoricalData(
            reqId,
            contract,
            end,
            durationStr,
            barSizeSetting,
            whatToShow,
            useRTH,
            formatDate,
            keepUpToDate,
            chartOptions,
        )
        task = asyncio.wait_for(future, timeout) if timeout else future
        try:
            await task
        except asyncio.TimeoutError:
            self.client.cancelHistoricalData(reqId)
            self._logger.warning(f"reqHistoricalData: Timeout for {contract}")
            bars.clear()
        return bars

    def reqHistoricalScheduleAsync(
        self,
        contract: Contract,
        numDays: int,
        endDateTime: Union[datetime, date, str, None] = "",
        useRTH: bool = True,
    ) -> Awaitable[HistoricalSchedule]:
        """

        :param contract: 
        :type contract: Contract
        :param numDays: 
        :type numDays: int
        :param endDateTime:  (Default value = "")
        :type endDateTime: Union[datetime, date, str, None]
        :param useRTH:  (Default value = True)
        :type useRTH: bool
        :rtype: Awaitable[HistoricalSchedule]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId, contract)
        end = util.formatIBDatetime(endDateTime)
        self.client.reqHistoricalData(
            reqId,
            contract,
            end,
            f"{numDays} D",
            "1 day",
            "SCHEDULE",
            useRTH,
            1,
            False,
            None,
        )
        return future

    def reqHistoricalTicksAsync(
        self,
        contract: Contract,
        startDateTime: Union[str, date],
        endDateTime: Union[str, date],
        numberOfTicks: int,
        whatToShow: str,
        useRth: bool,
        ignoreSize: bool = False,
        miscOptions: List[TagValue] = [],
    ) -> Awaitable[List]:
        """

        :param contract: 
        :type contract: Contract
        :param startDateTime: 
        :type startDateTime: Union[str, date]
        :param endDateTime: 
        :type endDateTime: Union[str, date]
        :param numberOfTicks: 
        :type numberOfTicks: int
        :param whatToShow: 
        :type whatToShow: str
        :param useRth: 
        :type useRth: bool
        :param ignoreSize:  (Default value = False)
        :type ignoreSize: bool
        :param miscOptions:  (Default value = [])
        :type miscOptions: List[TagValue]
        :rtype: Awaitable[List]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId, contract)
        start = util.formatIBDatetime(startDateTime)
        end = util.formatIBDatetime(endDateTime)
        self.client.reqHistoricalTicks(
            reqId,
            contract,
            start,
            end,
            numberOfTicks,
            whatToShow,
            useRth,
            ignoreSize,
            miscOptions,
        )
        return future

    async def reqHeadTimeStampAsync(
            self,
            contract: Contract,
            whatToShow: str,
            useRTH: bool,
            formatDate: int) -> datetime:
        """

        :param contract: 
        :type contract: Contract
        :param whatToShow: 
        :type whatToShow: str
        :param useRTH: 
        :type useRTH: bool
        :param formatDate: 
        :type formatDate: int
        :rtype: datetime

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId, contract)
        self.client.reqHeadTimeStamp(
            reqId, contract, whatToShow, useRTH, formatDate)
        await future
        self.client.cancelHeadTimeStamp(reqId)
        return future.result()

    def reqSmartComponentsAsync(self, bboExchange):
        """

        :param bboExchange: 

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId)
        self.client.reqSmartComponents(reqId, bboExchange)
        return future

    def reqMktDepthExchangesAsync(
            self) -> Awaitable[List[DepthMktDataDescription]]:
        """


        :rtype: Awaitable[List[DepthMktDataDescription]]

        """
        future = self.wrapper.startReq("mktDepthExchanges")
        self.client.reqMktDepthExchanges()
        return future

    def reqHistogramDataAsync(
        self, contract: Contract, useRTH: bool, period: str
    ) -> Awaitable[List[HistogramData]]:
        """

        :param contract: 
        :type contract: Contract
        :param useRTH: 
        :type useRTH: bool
        :param period: 
        :type period: str
        :rtype: Awaitable[List[HistogramData]]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId, contract)
        self.client.reqHistogramData(reqId, contract, useRTH, period)
        return future

    def reqFundamentalDataAsync(
        self,
        contract: Contract,
        reportType: str,
        fundamentalDataOptions: List[TagValue] = [],
    ) -> Awaitable[str]:
        """

        :param contract: 
        :type contract: Contract
        :param reportType: 
        :type reportType: str
        :param fundamentalDataOptions:  (Default value = [])
        :type fundamentalDataOptions: List[TagValue]
        :rtype: Awaitable[str]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId, contract)
        self.client.reqFundamentalData(
            reqId, contract, reportType, fundamentalDataOptions
        )
        return future

    async def reqScannerDataAsync(
        self,
        subscription: ScannerSubscription,
        scannerSubscriptionOptions: List[TagValue] = [],
        scannerSubscriptionFilterOptions: List[TagValue] = [],
    ) -> ScanDataList:
        """

        :param subscription: 
        :type subscription: ScannerSubscription
        :param scannerSubscriptionOptions:  (Default value = [])
        :type scannerSubscriptionOptions: List[TagValue]
        :param scannerSubscriptionFilterOptions:  (Default value = [])
        :type scannerSubscriptionFilterOptions: List[TagValue]
        :rtype: ScanDataList

        """
        dataList = self.reqScannerSubscription(
            subscription,
            scannerSubscriptionOptions or [],
            scannerSubscriptionFilterOptions or [],
        )
        future = self.wrapper.startReq(dataList.reqId, container=dataList)
        await future
        self.client.cancelScannerSubscription(dataList.reqId)
        return future.result()

    def reqScannerParametersAsync(self) -> Awaitable[str]:
        """


        :rtype: Awaitable[str]

        """
        future = self.wrapper.startReq("scannerParams")
        self.client.reqScannerParameters()
        return future

    async def calculateImpliedVolatilityAsync(
        self,
        contract: Contract,
        optionPrice: float,
        underPrice: float,
        implVolOptions: List[TagValue] = [],
    ) -> Optional[OptionComputation]:
        """

        :param contract: 
        :type contract: Contract
        :param optionPrice: 
        :type optionPrice: float
        :param underPrice: 
        :type underPrice: float
        :param implVolOptions:  (Default value = [])
        :type implVolOptions: List[TagValue]
        :rtype: Optional[OptionComputation]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId, contract)
        self.client.calculateImpliedVolatility(
            reqId, contract, optionPrice, underPrice, implVolOptions
        )
        try:
            await asyncio.wait_for(future, 4)
            return future.result()
        except asyncio.TimeoutError:
            self._logger.error("calculateImpliedVolatilityAsync: Timeout")
            return None
        finally:
            self.client.cancelCalculateImpliedVolatility(reqId)

    async def calculateOptionPriceAsync(
        self,
        contract: Contract,
        volatility: float,
        underPrice: float,
        optPrcOptions: List[TagValue] = [],
    ) -> Optional[OptionComputation]:
        """

        :param contract: 
        :type contract: Contract
        :param volatility: 
        :type volatility: float
        :param underPrice: 
        :type underPrice: float
        :param optPrcOptions:  (Default value = [])
        :type optPrcOptions: List[TagValue]
        :rtype: Optional[OptionComputation]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId, contract)
        self.client.calculateOptionPrice(
            reqId, contract, volatility, underPrice, optPrcOptions
        )
        try:
            await asyncio.wait_for(future, 4)
            return future.result()
        except asyncio.TimeoutError:
            self._logger.error("calculateOptionPriceAsync: Timeout")
            return None
        finally:
            self.client.cancelCalculateOptionPrice(reqId)

    def reqSecDefOptParamsAsync(
        self,
        underlyingSymbol: str,
        futFopExchange: str,
        underlyingSecType: str,
        underlyingConId: int,
    ) -> Awaitable[List[OptionChain]]:
        """

        :param underlyingSymbol: 
        :type underlyingSymbol: str
        :param futFopExchange: 
        :type futFopExchange: str
        :param underlyingSecType: 
        :type underlyingSecType: str
        :param underlyingConId: 
        :type underlyingConId: int
        :rtype: Awaitable[List[OptionChain]]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId)
        self.client.reqSecDefOptParams(
            reqId,
            underlyingSymbol,
            futFopExchange,
            underlyingSecType,
            underlyingConId)
        return future

    def reqNewsProvidersAsync(self) -> Awaitable[List[NewsProvider]]:
        """


        :rtype: Awaitable[List[NewsProvider]]

        """
        future = self.wrapper.startReq("newsProviders")
        self.client.reqNewsProviders()
        return future

    def reqNewsArticleAsync(
            self,
            providerCode: str,
            articleId: str,
            newsArticleOptions: List[TagValue] = []) -> Awaitable[NewsArticle]:
        """

        :param providerCode: 
        :type providerCode: str
        :param articleId: 
        :type articleId: str
        :param newsArticleOptions:  (Default value = [])
        :type newsArticleOptions: List[TagValue]
        :rtype: Awaitable[NewsArticle]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId)
        self.client.reqNewsArticle(
            reqId, providerCode, articleId, newsArticleOptions)
        return future

    async def reqHistoricalNewsAsync(
        self,
        conId: int,
        providerCodes: str,
        startDateTime: Union[str, date],
        endDateTime: Union[str, date],
        totalResults: int,
        historicalNewsOptions: List[TagValue] = [],
    ) -> Optional[HistoricalNews]:
        """

        :param conId: 
        :type conId: int
        :param providerCodes: 
        :type providerCodes: str
        :param startDateTime: 
        :type startDateTime: Union[str, date]
        :param endDateTime: 
        :type endDateTime: Union[str, date]
        :param totalResults: 
        :type totalResults: int
        :param historicalNewsOptions:  (Default value = [])
        :type historicalNewsOptions: List[TagValue]
        :rtype: Optional[HistoricalNews]

        """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId)
        start = util.formatIBDatetime(startDateTime)
        end = util.formatIBDatetime(endDateTime)
        self.client.reqHistoricalNews(
            reqId,
            conId,
            providerCodes,
            start,
            end,
            totalResults,
            historicalNewsOptions)
        try:
            await asyncio.wait_for(future, 4)
            return future.result()
        except asyncio.TimeoutError:
            self._logger.error("reqHistoricalNewsAsync: Timeout")
            return None

    async def requestFAAsync(self, faDataType: int):
        """

        :param faDataType: 
        :type faDataType: int

        """
        future = self.wrapper.startReq("requestFA")
        self.client.requestFA(faDataType)
        try:
            await asyncio.wait_for(future, 4)
            return future.result()
        except asyncio.TimeoutError:
            self._logger.error("requestFAAsync: Timeout")

    async def getWshMetaDataAsync(self) -> str:
        """


        :rtype: str

        """
        if self.wrapper.wshMetaReqId:
            self.cancelWshMetaData()
        self.reqWshMetaData()
        future = self.wrapper.startReq(self.wrapper.wshMetaReqId, container="")
        await future
        return future.result()

    async def getWshEventDataAsync(self, data: WshEventData) -> str:
        """

        :param data: 
        :type data: WshEventData
        :rtype: str

        """
        if self.wrapper.wshEventReqId:
            self.cancelWshEventData()
        self.reqWshEventData(data)
        future = self.wrapper.startReq(
            self.wrapper.wshEventReqId, container="")
        await future
        self.cancelWshEventData()
        return future.result()

    def reqUserInfoAsync(self):
        """ """
        reqId = self.client.getReqId()
        future = self.wrapper.startReq(reqId)
        self.client.reqUserInfo(reqId)
        return future
