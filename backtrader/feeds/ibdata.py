"""ibdata.py module.

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
import threading
import time

import backtrader as bt
from backtrader import TimeFrame, date2num, num2date
from backtrader.commissions.ibcommission import IBCommInfo
from backtrader.feed import DataBase
from backtrader.stores import ibstore_insync
from backtrader.utils.py3 import (
    integer_types,
    string_types,
    with_metaclass,
)
from dateutil.relativedelta import relativedelta


class MetaIBData(DataBase.__class__):
""""""
"""Class has already been created ... register

Args::
    name: 
    bases: 
    dct:"""
    dct:"""
        # Initialize the class
        super(MetaIBData, cls).__init__(name, bases, dct)

        # Register with the store
        # ibstore.IBStore.DataCls = cls
        ibstore_insync.IBStoreInsync.DataCls = cls


class IBData(with_metaclass(MetaIBData, DataBase)):
    """Interactive Brokers Data Feed.
Supports the following contract specifications in parameter ``dataname``:
Pattern: secType-others
BONDS & CFDs & CommoditiesCopy & CryptocurrencyCopy & Continuous Futures *
Forex Pairs & IndicesCopy & Mutual Funds & STK & Standard Warrants:
secType-symbol-currency-exchange-primaryExchange(only for STK)
BOND-912828C57-USD-SMART
CFD-IBDE30-EUR-SMART
CMDTY-XAUUSD-USD-SMART
CRYPTO-ETH-USD-PAXOS
CONTFUT-ES-USD-CME
CASH-EUR-GBP-IDEALPRO
IND-DAX-EUR-EUREX
FUND-VINIX-USD-FUNDSERV
STK-AAPL-USD-SMART
STK-SPY-USD-SMART-ARCA
STK-EMCGU-USD-SMART #Stock Contract with IPO price
IOPT-B881G-EUR-SBF
Contracts specified by CUSIP, FIGI, or ISIN
secIdType-secId-exchange
FIGI-BBG000B9XRY4-SMART
Futures
secType-symbol-currency-exchange-lastTradeDateOrContractMonth-multiplier-IncludeExpired
FUT-ES-USD-CME-'202809'-50-False
FUT-ES-USD-CME-'202309'-None-True
Futures Options
secType-symbol-currency-exchange-lastTradeDateOrContractMonth-multiplier-strike-right
FOP-GBL-EUR-EUREX-'20230224'-'1000'-138-C
Options & Dutch Warrants and Structured Products
secType-symbol-currency-exchange-lastTradeDateOronth-multiplier-strike-right
OPT-GOOG-USD-BOX-'20190315'-'100'-1180-C
WAR-GOOG-EUR-FWB-20201117-'001'-15000-C"""

    params = (
        ("secType", "STK"),  # usual industry value
        ("exchange", "SMART"),  # usual industry value
        ("primaryExchange", None),  # native exchange of the contract
        ("right", None),  # Option or Warrant Call('C') or Put('P')
        ("strike", None),  # Future, Option or Warrant strike price
        ("multiplier", None),  # Future, Option or Warrant multiplier
        (
            "expiry",
            None,
        ),  # Future, Option or Warrant lastTradeDateOrContractMonth date
        ("currency", ""),  # currency for the contract
        ("localSymbol", None),  # Warrant localSymbol override
        ("rtbar", False),  # use RealTime 5 seconds bars
        ("historical", False),  # only historical download
        (
            "durationStr",
            "1 W",
            # historical - The amount of time to go back from the request’s
            # given enddatetime.
        ),
        (
            "barSizeSetting",
            "4 hours",
        ),  # historical - The data’s granularity or Valid Bar Sizes
        ("what", None),  # historical - what to show
        ("useRTH", False),  # historical - download only Regular Trading Hours
        (
            "formatDate",
            1,
            # historical -  The format in which the incoming bars’ date should
            # be presented.
        ),
        (
            "keepUpToDate",
            False,
        ),  # historical -  Whether a subscription is made to return
        ("qcheck", 0.5),  # timeout in seconds (float) to check for events
        ("backfill_start", True),  # do backfilling at the start
        ("backfill", True),  # do backfilling when reconnecting
        ("backfill_from", None),  # additional data source to do backfill from
        ("latethrough", False),  # let late samples through
        ("tradename", None),  # use a different asset as order target
        (
            "numberOfTicks",
            1000,
        ),  # Number of distinct data points. Max is 1000 per request.
        (
            "ignoreSize",
            False,
            # Omit updates that reflect only changes in size, and not price.
            # Applicable to Bid_Ask data requests.
        ),
    )

    _IBCommissionTypes = {
        None: IBCommInfo.COMM_FIXED,  # default
        "STK": IBCommInfo.COMM_STOCK,
        "FUT": IBCommInfo.COMM_FUTURE,
        "OPT": IBCommInfo.COMM_OPTION,
        "CASH": IBCommInfo.COMM_FOREX,
    }

    _IBFUTMargin = {
        "M6E": {"Initial": 374.049, "Maintenance": 325.26},
        "M6B": {"Initial": 272.374, "Maintenance": 236.847},
        "M6A": {"Initial": 261.883, "Maintenance": 227.725},
        "MSF": {"Initial": 488.304, "Maintenance": 424.6125},
        "MCD": {"Initial": 169.445, "Maintenance": 147.343},
        "MJY": {"Initial": 377.996, "Maintenance": 328.692},
    }

    # _store = ibstore.IBStore
    _store = ibstore_insync.IBStoreInsync

    # Minimum size supported by real-time bars
    RTBAR_MINSIZE = (TimeFrame.Seconds, 5)

    # States for the Finite State Machine in _load
    _ST_FROM, _ST_START, _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(5)

    def _timeoffset(self):
""""""
""""""
"""Returns ``True`` to notify ``Cerebro`` that preloading and runonce
        should be deactivated"""
        """
        return not self.p.historical

    def __init__(self, **kwargs):
        """"""
        self.ib = self._store(**kwargs)
        self.precontract = self.parsecontract(self.p.dataname)
        self.pretradecontract = self.parsecontract(self.p.tradename)
        self.constractStartDate = None  # 用于保存合约开始日期，data/datetime
        self.commission = None  # 用于保存数据对应的佣金信息,在生成对应合同时初始化
        self._lock_q = threading.Condition()  # sync access to qlive

    def caldate(self):
""""""
"""Receives an environment (cerebro) and passes it over to the store it
belongs to

Args::
    env:"""
    env:"""
        super(IBData, self).setenvironment(env)
        env.addstore(self.ib)

    CONTRACT_TYPE = [
        "BOND",
        "CFD",
        "CMDTY",
        "CRYPTO",
        "CONTFUT",
        "CASH",
        "IND",
        "FUND",
        "STK",
        "IOPT",
        "FIGI",
        "CUSIP",
        "ISIN",
        "FUT",
        "FOP",
        "OPT",
        "WAR",
    ]

    def parsecontract(self, dataname):
"""Parses dataname generates a default contract
Pattern: secType-others
BONDS & CFDs & CommoditiesCopy & CryptocurrencyCopy & Continuous Futures *
Forex Pairs & IndicesCopy & Mutual Funds & STK & Standard Warrants:
secType-symbol-currency-exchange-primaryExchange(only for STK)
BOND-122014AJ2-USD-SMART    #EndData=datetime(2024, 5, 16) / ''
CFD-IBUS30-USD-SMART    #EndData=datetime(2014, 12, 31) / ''
CMDTY-XAUUSD-USD-SMART  #EndData=datetime(2024, 5, 16) / ''
CRYPTO-ETH-USD-PAXOS    #EndData=datetime(2024, 5, 16) / ''
CONTFUT-ES-USD-CME  #'', Not supoort EndData
CASH-EUR-GBP-IDEALPRO   #EndData=datetime(2024, 5, 16) / ''
IND-DAX-EUR-EUREX   #EndData=datetime(2014, 12, 31) / '', not support bid/ask
FUND-VWELX-USD-FUNDSERV #EndData=datetime(2014, 12, 31) / '', only support trades
STK-AAPL-USD-SMART  #EndData=datetime(2014, 12, 31) / ''
STK-SPY-USD-SMART-ARCA  #EndData=datetime(2014, 12, 31) / ''
STK-EMCGU-USD-SMART #Stock Contract with IPO price  #EndData=datetime(2024, 5, 16) / ''
IOPT-B881G-EUR-SBF #Not Found suitable example for IOPT
Contracts specified by CUSIP, FIGI, or ISIN
secIdType-secId-exchange
FIGI-BBG000B9XRY4-SMART
Futures
secType-symbol-currency-exchange-lastTradeDateOrContractMonth-multiplier-IncludeExpired
FUT-ES-USD-CME-202809-50-False  #EndData=datetime(2024, 5, 16) / ''
FUT-ES-USD-CME-202309-None-True #not supported
Futures Options
secType-symbol-currency-exchange-lastTradeDateOrContractMonth-multiplier-strike-right
FOP-GBL-EUR-EUREX-'20230224'-'1000'-138-C
OPT-GOOG-USD-SMART-20241220-100-180-C #EndData=datetime(2024, 10, 16) / '' 1M 1hour
WAR-GOOG-EUR-FWB-20201117-001-15000-C

Args::
    dataname:"""
    dataname:"""

        # Set defaults for optional tokens in the ticker string
        if dataname is None:
            return None

        # Make the initial contract
        precon = self.ib.makecontract()

        # split the ticker string
        tokens = iter(dataname.split("-"))

        # Symbol and security type are compulsory
        sectype = next(tokens)

        assert sectype in self.CONTRACT_TYPE

        if sectype in ["CUSIP", "FIGI", "ISIN"]:
            precon.secIdType = self.p.secType = sectype
            precon.secId = next(tokens)
            precon.exchange = self.p.exchange = next(tokens)
        else:
            precon.secType = self.p.secType = sectype
            if sectype == "IOPT":
                precon.localsymbol = self.p.localsymbol = next(tokens)
            else:
                precon.symbol = self.p.symbol = next(tokens)
            precon.currency = self.p.currency = next(tokens)
            precon.exchange = self.p.exchange = next(tokens)

            if sectype == "STK":
                try:
                    precon.primaryExchange = self.p.primaryExchange = next(tokens)
                except StopIteration:
                    pass
            elif sectype in ["FUT", "FOP", "OPT", "WAR"]:
                expiry = next(tokens)
                multiplier = next(tokens)
                strike = next(tokens)
                if sectype == "FUT":
                    precon.lastTradeDateOrContractMonth = self.p.expiry = expiry
                    precon.IncludeExpired = self.p.IncludeExpired = bool(
                        strike
                    )  # 只是同一位置，变量名与实际变更不一致
                    if multiplier != "None":
                        precon.multiplier = self.p.multiplier = multiplier
                else:
                    precon.lastTradeDateOrContractMonth = self.p.expiry = expiry
                    precon.multiplier = self.p.multiplier = multiplier
                    precon.strike = self.p.strike = int(strike)
                    precon.right = self.p.right = next(tokens)

        print(f"precon= {precon}")
        return precon

    def updatecomminfo(self, contract=None):
"""Args::
    contract: (Default value = None)"""
"""Starts the IB connecction and gets the real contract and
        contractdetails if it exists"""
        """
        super(IBData, self).start()
        # Kickstart store and get queue to wait on
        self.qlive = self.ib.start(data=self)
        self.qhist = None

        self._usertvol = not self.p.rtbar
        tfcomp = (self._timeframe, self._compression)
        if tfcomp < self.RTBAR_MINSIZE:
            # Requested timeframe/compression not supported by rtbars
            self._usertvol = True

        self.contract = None
        self.contractdetails = None
        self.tradecontract = None
        self.tradecontractdetails = None

        if self.p.backfill_from is not None:
            self._state = self._ST_FROM
            self.p.backfill_from.setenvironment(self._env)
            self.p.backfill_from._start()
        else:
            self._state = self._ST_START  # initial state for _load
        self._statelivereconn = False  # if reconnecting in live state
        self._subcription_valid = False  # subscription state
        self._storedmsg = dict()  # keep pending live message (under None)

        if not self.ib.isConnected():
            return

        self.put_notification(self.CONNECTED)
        # get real contract details with real conId (contractId)
        cds = self.ib.reqContractDetails(self.precontract)
        assert len(cds) == 1

        if cds is not None:
            cdetails = cds[0]
            self.contract = cdetails.contract
            self.contractdetails = cdetails
            self.constractStartDateUTC = self.ib.reqHeadTimeStamp(
                contract=self.contract,
                whatToShow="TRADES",
                useRTH=1,
                formatDate=1,
            )  # format=1 UTC time format=2 epoch time
            self.updatecomminfo(self.contract)
        else:
            # no contract can be found (or many)
            self.put_notification(self.DISCONNECTED)
            return

        if self.pretradecontract is None:
            # no different trading asset - default to standard asset
            self.tradecontract = self.contract
            self.tradecontractdetails = self.contractdetails
        else:
            # different target asset (typical of some CDS products)
            # use other set of details
            cds = self.ib.getContractDetails(self.pretradecontract, maxcount=1)
            if cds is not None:
                cdetails = cds[0]
                self.tradecontract = cdetails.contract
                self.tradecontractdetails = cdetails
            else:
                # no contract can be found (or many)
                self.put_notification(self.DISCONNECTED)
                return

        if self._state == self._ST_START:
            self._start_finish()  # to finish initialization
            self._st_start()

    def reqdata(self):
        """request real-time data. checks cash vs non-cash) and param useRT"""
        if self.contract is None or self._subcription_valid:
            return

        if self._usertvol and self._timeframe != bt.TimeFrame.Ticks:
            self.qlive = self.ib.reqMktData(self.contract, self.p.what)
        elif self._usertvol and self._timeframe == bt.TimeFrame.Ticks:
            self.qlive = self.ib.reqTickByTickData(self.contract, self.p.what)
        else:
            self.qlive = self.ib.reqRealTimeBars(
                contract=self.contract,
                barSize=5,
                whatToShow=self.p.what,
                useRTH=self.p.useRTH,
            )
            self.qlive.updateEvent += self.onliveupdate

        self._subcription_valid = True
        return self.qlive

    def canceldata(self):
        """Cancels Market Data subscription, checking asset type and rtbar"""
        if self.contract is None:
            return

        if self._usertvol and self._timeframe != bt.TimeFrame.Ticks:
            self.ib.cancelMktData(self.qlive)
        elif self._usertvol and self._timeframe == bt.TimeFrame.Ticks:
            self.ib.cancelTickByTickData(self.qlive)
        else:
            self.ib.cancelRealTimeBars(self.qlive)

    def haslivedata(self):
""""""
"""Args::
    step: (Default value = 0)
    bars: (Default value = None)
    hist: (Default value = True)"""
    hist: (Default value = True)"""
        for bar in bars:
            len(self.lines.close)
            self.forward()
            self._load_rtbar(bar, hist=hist)

    def onliveupdate(self, bars, hasNewBar):
"""Args::
    bars: 
    hasNewBar:"""
    hasNewBar:"""
        # 对于hisorical数据，bars保存reqhistoricaEnd开始的所有数据
        # bars长度为0，表示未接收到update数据
        # bars最后一个数据为临时数据，5秒更新一次，保存最新收到的update数据，只有当timeframe时间到了才后固定
        if self.p.historical:
            newdatalen = len(bars)

            if newdatalen < 2:  # 无数据或仅有一个数据，不处理。
                return

            if hasNewBar:
                bars[-1].date
                if newdatalen == 2:
                    print(f"onliveupdate size:1 bar.date:{bars[0].date}")
                else:
                    print(
                        f"onliveupdate size:{newdatalen - 1} from {bars[0].date} to"
                        f" {bars[-2].date}"
                    )
                # 有2个以上数据,按timeframe频率更新，避免频率重复调用,一直更新到倒数第2个数据，仅保存最后一个数据:-1不包含-1，只到-2
                self.updatelivedata(newdatalen - 1, bars[:-1])
                bars[:] = bars[-1:]
        else:
            with self._lock_q:
                self._lock_q.notify()

    def _load(self):
""""""
""""""
""""""
"""Args::
    rtbar: 
    hist: (Default value = False)"""
    hist: (Default value = False)"""
        # A complete 5 second bar made of real-time ticks is delivered and
        # contains open/high/low/close/volume prices
        # The historical data has the same data but with 'date' instead of
        # 'time' for datetime
        # print(f'_load_rtbar rtbar:{rtbar}')
        dt = date2num(rtbar.time if not hist else rtbar.date)
        if dt < self.lines.datetime[-1] and not self.p.latethrough:
            return False  # cannot deliver earlier than already delivered

        self.lines.datetime[0] = dt
        # Put the tick into the bar
        if hist is False:
            self.lines.open[0] = rtbar.open_
        else:
            self.lines.open[0] = rtbar.open
        self.lines.high[0] = rtbar.high
        self.lines.low[0] = rtbar.low
        self.lines.close[0] = rtbar.close
        self.lines.volume[0] = rtbar.volume
        self.lines.openinterest[0] = 0

        return True

    def _load_rtvolume(self, rtvol):
"""Args::
    rtvol:"""
"""Args::
    tick: 
    hist: (Default value = False)"""
    hist: (Default value = False)"""

        dt = date2num(tick.datetime if not hist else tick.date)
        if dt < self.lines.datetime[-1] and not self.p.latethrough:
            return False  # cannot deliver earlier than already delivered

        self.lines.datetime[0] = dt

        if tick.dataType == "RT_TICK_MIDPOINT":
            self.lines.close[0] = tick.midPoint
        elif tick.dataType == "RT_TICK_BID_ASK":
            self.lines.open[0] = tick.bidPrice
            self.lines.close[0] = tick.askPrice
            self.lines.volume[0] = tick.bidSize
            self.lines.openinterest[0] = tick.askSize
        elif tick.dataType == "RT_TICK_LAST":
            self.lines.close[0] = tick.price
            self.lines.volume[0] = tick.size

        return True
