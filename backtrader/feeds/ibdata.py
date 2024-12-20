#!/usr/tzbin/env python
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
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
from dateutil.relativedelta import relativedelta

import backtrader as bt
from backtrader.feed import DataBase
from backtrader import TimeFrame, date2num, num2date
from backtrader.utils.py3 import (integer_types, queue, string_types,
                                  with_metaclass)
from backtrader.metabase import MetaParams
from backtrader.stores import ibstore, ibstore_insync


class MetaIBData(DataBase.__class__):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaIBData, cls).__init__(name, bases, dct)

        # Register with the store
        ibstore.IBStore.DataCls = cls
        ibstore_insync.IBStoreInsync.DataCls = cls

class IBData(with_metaclass(MetaIBData, DataBase)):
    '''Interactive Brokers Data Feed.

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
            WAR-GOOG-EUR-FWB-20201117-'001'-15000-C

             

    Params:

      - ``sectype`` (default: ``STK``)

        Default value to apply as *security type* if not provided in the
        ``dataname`` specification

      - ``exchange`` (default: ``SMART``)

        Default value to apply as *exchange* if not provided in the
        ``dataname`` specification

      - ``primaryExchange`` (default: ``None``)

        For certain smart-routed stock contracts that have the same symbol, 
        currency and exchange, you would also need to specify the primary 
        exchange attribute to uniquely define the contract. This should be 
        defined as the native exchange of a contract

      - ``right`` (default: ``None``)

        Warrants, like options, require an expiration date, a right, 
        a strike and an optional multiplier.

      - ``strike`` (default: ``None``)

        Warrants, like options, require an expiration date, a right, 
        a strike and an optional multiplier.

      - ``expiry`` (default: ``None``)

        Warrants, like options, require an expiration date, a right, 
        a strike and an optional multiplier.
        In this case expiry is 'lastTradeDateOrContractMonth'
      - ``currency`` (default: ``''``)

        Default value to apply as *currency* if not provided in the
        ``dataname`` specification

      - ``multiplier`` (default: ``None``)

        Occasionally, you can expect to have more than a single future 
        contract for the same underlying with the same expiry. To rule 
        out the ambiguity, the contract's multiplier can be given

      - ``tradingClass`` (default: ``None``)

        It is not unusual to find many option contracts with an almost identical 
        description (i.e. underlying symbol, strike, last trading date, 
        multiplier, etc.). Adding more details such as the trading class will help

      - ``localSymbol`` (default: ``None``)

        Warrants, like options, require an expiration date, a right, a strike and 
        a multiplier. For some warrants it will be necessary to define a 
        localSymbol or conId to uniquely identify the contract
      - ``historical`` (default: ``False``)

        If set to ``True`` the data feed will stop after doing the first
        download of data.

        The standard data feed parameters ``fromdate`` and ``todate`` will be
        used as reference.

        The data feed will make multiple requests if the requested duration is
        larger than the one allowed by IB given the timeframe/compression
        chosen for the data.

      - ``what`` (default: ``None``)

        If ``None`` the default for different assets types will be used for
        historical data requests:

          - 'BID' for CASH assets
          - 'TRADES' for any other

        Use 'ASK' for the Ask quote of cash assets
        
        Check the IB API docs if another value is wished
        (TRADES,MIDPOINT,BID,ASK,BID_ASK,ADJUSTED_LAST,HISTORICAL_VOLATILITY,
         OPTION_IMPLIED_VOLATILITY, REBATE_RATE, FEE_RATE,
         YIELD_BID, YIELD_ASK, YIELD_BID_ASK, YIELD_LAST)

      - ``rtbar`` (default: ``False``)

        If ``True`` the ``5 Seconds Realtime bars`` provided by Interactive
        Brokers will be used as the smalles tick. According to the
        documentation they correspond to real-time values (once collated and
        curated by IB)

        If ``False`` then the ``RTVolume`` prices will be used, which are based
        on receiving ticks. In the case of ``CASH`` assets (like for example
        EUR.JPY) ``RTVolume`` will always be used and from it the ``bid`` price
        (industry de-facto standard with IB according to the literature
        scattered over the Internet)

        Even if set to ``True``, if the data is resampled/kept to a
        timeframe/compression below Seconds/5, no real time bars will be used,
        because IB doesn't serve them below that level

      - ``qcheck`` (default: ``0.5``)

        Time in seconds to wake up if no data is received to give a chance to
        resample/replay packets properly and pass notifications up the chain

      - ``backfill_start`` (default: ``True``)

        Perform backfilling at the start. The maximum possible historical data
        will be fetched in a single request.

      - ``backfill`` (default: ``True``)

        Perform backfilling after a disconnection/reconnection cycle. The gap
        duration will be used to download the smallest possible amount of data

      - ``backfill_from`` (default: ``None``)

        An additional data source can be passed to do an initial layer of
        backfilling. Once the data source is depleted and if requested,
        backfilling from IB will take place. This is ideally meant to backfill
        from already stored sources like a file on disk, but not limited to.

      - ``latethrough`` (default: ``False``)

        If the data source is resampled/replayed, some ticks may come in too
        late for the already delivered resampled/replayed bar. If this is
        ``True`` those ticks will bet let through in any case.

        Check the Resampler documentation to see who to take those ticks into
        account.

        This can happen especially if ``timeoffset`` is set to ``False``  in
        the ``IBStore`` instance and the TWS server time is not in sync with
        that of the local computer

      - ``tradename`` (default: ``None``)
        Useful for some specific cases like ``CFD`` in which prices are offered
        by one asset and trading happens in a different onel

        - SPY-STK-SMART-USD -> SP500 ETF (will be specified as ``dataname``)

        - SPY-CFD-SMART-USD -> which is the corresponding CFD which offers not
          price tracking but in this case will be the trading asset (specified
          as ``tradename``)

    The default values in the params are the to allow things like ```TICKER``,
    to which the parameter ``secType`` (default: ``STK``) and ``exchange``
    (default: ``SMART``) are applied.

    Some assets like ``AAPL`` need full specification including ``currency``
    (default: '') whereas others like ``TWTR`` can be simply passed as it is.

      - ``AAPL-STK-SMART-USD`` would be the full specification for dataname

        Or else: ``IBData`` as ``IBData(dataname='AAPL', currency='USD')``
        which uses the default values (``STK`` and ``SMART``) and overrides
        the currency to be ``USD``
    '''
    params = (
        ('secType', 'STK'),  # usual industry value
        ('exchange', 'SMART'),  # usual industry value
        ('primaryExchange', None),  # native exchange of the contract
        ('right', None),  # Option or Warrant Call('C') or Put('P')
        ('strike', None),  # Future, Option or Warrant strike price
        ('multiplier', None),  # Future, Option or Warrant multiplier
        ('expiry', None),  # Future, Option or Warrant lastTradeDateOrContractMonth date 
        ('currency', ''),  # currency for the contract
        ('localSymbol', None),  # Warrant localSymbol override
        ('rtbar', False),  # use RealTime 5 seconds bars
        ('historical', False),  # only historical download
        ('durationStr', '1 W'), #historical - The amount of time to go back from the request’s given enddatetime.
        ('barSizeSetting', '4 hours'),   # historical - The data’s granularity or Valid Bar Sizes
        ('what', None),  # historical - what to show
        ('useRTH', False),  # historical - download only Regular Trading Hours
        ('formatDate', 1),  # historical -  The format in which the incoming bars’ date should be presented. 
        ('keepUpToDate', False),    # historical -  Whether a subscription is made to return 
        ('qcheck', 0.5),  # timeout in seconds (float) to check for events
        ('backfill_start', True),  # do backfilling at the start
        ('backfill', True),  # do backfilling when reconnecting
        ('backfill_from', None),  # additional data source to do backfill from
        ('latethrough', False),  # let late samples through
        ('tradename', None),  # use a different asset as order target
        ('numberOfTicks', 1000),  # Number of distinct data points. Max is 1000 per request.
        ('ignoreSize', False),  # Omit updates that reflect only changes in size, and not price. Applicable to Bid_Ask data requests.
    )

    #_store = ibstore.IBStore
    _store = ibstore_insync.IBStoreInsync

    # Minimum size supported by real-time bars
    RTBAR_MINSIZE = (TimeFrame.Seconds, 5)

    # States for the Finite State Machine in _load
    _ST_FROM, _ST_START, _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(5)

    def _timeoffset(self):
        return self.ib.timeoffset()

    def _gettz(self):
        # If no object has been provided by the user and a timezone can be
        # found via contractdtails, then try to get it from pytz, which may or
        # may not be available.

        # The timezone specifications returned by TWS seem to be abbreviations
        # understood by pytz, but the full list which TWS may return is not
        # documented and one of the abbreviations may fail
        tzstr = isinstance(self.p.tz, string_types)
        if self.p.tz is not None and not tzstr:
            return bt.utils.date.Localizer(self.p.tz)

        if self.contractdetails is None:
            return None  # nothing can be done

        try:
            import pytz  # keep the import very local
        except ImportError:
            return None  # nothing can be done

        tzs = self.p.tz if tzstr else self.contractdetails.timeZoneId

        if tzs == 'CST':  # reported by TWS, not compatible with pytz. patch it
            tzs = 'CST6CDT'

        try:
            tz = pytz.timezone(tzs)
        except pytz.UnknownTimeZoneError:
            return None  # nothing can be done

        # contractdetails there, import ok, timezone found, return it
        return tz

    def islive(self):
        '''Returns ``True`` to notify ``Cerebro`` that preloading and runonce
        should be deactivated'''
        return not self.p.historical

    def __init__(self, **kwargs):
        self.ib = self._store(**kwargs)
        self.precontract = self.parsecontract(self.p.dataname)
        self.pretradecontract = self.parsecontract(self.p.tradename)
        self.constractStartDate = None  # 用于保存合约开始日期，data/datetime

    def caldate(self):
        duranumber = int(self.p.durationStr.split()[0])
        duraunit = self.p.durationStr.split()[1]
        
        todate = self.p.todate

        if self.p.todate == '':
            todate = datetime.datetime.now()
        elif isinstance(self.p.todate, datetime.date):
            # push it to the end of the day, or else intraday
            # values before the end of the day would be gone
            if not hasattr(self.p.todate, 'hour'):
                todate = self.p.todate = datetime.datetime.combine(
                    self.p.todate, self.p.sessionend)
                
        units_map = {
            'Y': 'years',
            'M': 'months',
            'W': 'weeks',
            'D': 'days',
            'S': 'seconds'
            }


        kwargs = {units_map[duraunit]: duranumber}
        self.p.fromdate = todate - relativedelta(**kwargs)

    def setenvironment(self, env):
        '''Receives an environment (cerebro) and passes it over to the store it
        belongs to'''
        super(IBData, self).setenvironment(env)
        env.addstore(self.ib)

    CONTRACT_TYPE = [
        'BOND', 'CFD', 'CMDTY', 'CRYPTO', 'CONTFUT', 'CASH', 'IND', 'FUND',
        'STK', 'IOPT', 'FIGI', 'CUSIP', 'ISIN', 'FUT', 'FOP', 'OPT', 'WAR']
    def parsecontract(self, dataname):
        '''
        Parses dataname generates a default contract
        
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
        '''

        # Set defaults for optional tokens in the ticker string
        if dataname is None:
            return None

        # Make the initial contract
        precon = self.ib.makecontract()

        # split the ticker string
        tokens = iter(dataname.split('-'))

        # Symbol and security type are compulsory
        sectype = next(tokens)

        assert sectype in self.CONTRACT_TYPE

        if sectype in ['CUSIP', 'FIGI', 'ISIN']:
            precon.secIdType = self.p.secType = sectype
            precon.secId = next(tokens)
            precon.exchange = self.p.exchange = next(tokens)
        else:
            precon.secType = self.p.secType = sectype
            if sectype == 'IOPT':
                precon.localsymbol = self.p.localsymbol = next(tokens)
            else:
                precon.symbol = self.p.symbol = next(tokens)
            precon.currency = self.p.currency = next(tokens)
            precon.exchange = self.p.exchange = next(tokens)

            if sectype == 'STK':
                try:
                    precon.primaryExchange = self.p.primaryExchange = next(tokens)
                except StopIteration:
                    pass
            elif sectype in ['FUT', 'FOP', 'OPT', 'WAR']:
                expiry = next(tokens)
                multiplier = next(tokens)
                strike = next(tokens)
                if sectype == 'FUT':
                    precon.lastTradeDateOrContractMonth = self.p.expiry = expiry
                    precon.IncludeExpired = self.p.IncludeExpired = bool(strike) #只是同一位置，变量名与实际变更不一致
                    if multiplier != 'None':
                        precon.multiplier = self.p.multiplier = multiplier
                else:
                    precon.lastTradeDateOrContractMonth = self.p.expiry = expiry
                    precon.multiplier = self.p.multiplier = multiplier
                    precon.strike = self.p.strike = int(strike)
                    precon.right = self.p.right = next(tokens)


        print(f'precon= {precon}')
        return precon

    def start(self):
        '''Starts the IB connecction and gets the real contract and
        contractdetails if it exists'''
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
        assert len(cds)==1
        
        if cds is not None:
            cdetails = cds[0]
            self.contract = cdetails.contract
            self.contractdetails = cdetails
            self.constractStartDateUTC = self.ib.reqHeadTimeStamp(
                contract=self.contract,
                whatToShow="TRADES", 
                useRTH=1, 
                formatDate=1
                ) #format=1 UTC time format=2 epoch time
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

    def stop(self):
        '''Stops and tells the store to stop'''
        super(IBData, self).stop()
        self.ib.stop()

    def reqdata(self):
        '''request real-time data. checks cash vs non-cash) and param useRT'''
        if self.contract is None or self._subcription_valid:
            return

        if self._usertvol and self._timeframe != bt.TimeFrame.Ticks:
            self.qlive = self.ib.reqMktData(self.contract, self.p.what)
        elif self._usertvol and self._timeframe == bt.TimeFrame.Ticks:
            self.qlive = self.ib.reqTickByTickData(self.contract, self.p.what)
        else:
            self.qlive = self.ib.reqRealTimeBars(contract=self.contract, barSize=5, whatToShow= self.p.what, useRTH=self.p.useRTH)
            self.qlive.updateEvent += self.onliveupdate


        self._subcription_valid = True
        return self.qlive

    def canceldata(self):
        '''Cancels Market Data subscription, checking asset type and rtbar'''
        if self.contract is None:
            return

        if self._usertvol and self._timeframe != bt.TimeFrame.Ticks:
            self.ib.cancelMktData(self.qlive)
        elif self._usertvol and self._timeframe == bt.TimeFrame.Ticks:
            self.ib.cancelTickByTickData(self.qlive)
        else:
            self.ib.cancelRealTimeBars(self.qlive)

    def haslivedata(self):
        return bool(self._storedmsg or self.qlive)

    def updatelivedata(self, step=0, bars=None):
        for bar in bars:
            d = len(self.lines.close)
            self.forward()
            self._load_rtbar(bar, hist=True)
            
        #print(f"add live data from{bars[0].date} to {bars[-1].date}, total:{len(bars)}")    
        self.getenvironment().start_barupdate(item=f'{d}') #通知cerebor进行处理，批处理，全更新完后处理一次

    def onliveupdate(self, bars, hasNewBar):
        # 对于hisorical数据，bars保存reqhistoricaEnd开始的所有数据
        # bars长度为0，表示未接收到update数据
        # bars最后一个数据为临时数据，5秒更新一次，保存最新收到的update数据，只有当timeframe时间到了才后固定

        newdatalen = len(bars)

        if newdatalen < 2: #无数据或仅有一个数据，不处理。
            return
        
        if hasNewBar:
            curtime = bars[-1].date
            if newdatalen==2:
                print(f"onliveupdate size:1 bar.date:{bars[0].date}")
            else:
                print(f"onliveupdate size:{newdatalen-1} from {bars[0].date} to {bars[-2].date}")  
            self.updatelivedata(newdatalen-1, bars[:-1]) #有2个以上数据,按timeframe频率更新，避免频率重复调用,一直更新到倒数第2个数据，仅保存最后一个数据:-1不包含-1，只到-2
            bars[:] = bars[-1:]


    def _load(self):
        if self.contract is None or self._state == self._ST_OVER:
            return False  # nothing can be done

        while True:
            if self._state == self._ST_LIVE:
                try:
                    msg = (self._storedmsg.pop(None, None) or
                           self.qlive.pop(0))
                except Exception as e:
                    #print("_load live data Exception:", e)
                    return None

                if msg is None:  # Conn broken during historical/backfilling
                    self._subcription_valid = False
                    self.put_notification(self.CONNBROKEN)
                    # Try to reconnect
                    if not self.ib.reconnect(resub=True):
                        self.put_notification(self.DISCONNECTED)
                        return False  # failed

                    self._statelivereconn = self.p.backfill
                    continue
                
                if msg == -504:  # Conn broken during live
                    self._subcription_valid = False
                    self.put_notification(self.CONNBROKEN)
                    # Try to reconnect
                    if not self.ib.reconnect(resub=True):
                        self.put_notification(self.DISCONNECTED)
                        return False  # failed

                    # self._statelivereconn = self.p.backfill
                    continue
                if msg == -354:
                    self.put_notification(self.NOTSUBSCRIBED)
                    return False

                elif msg == -1100:  # conn broken
                    # Tell to wait for a message to do a backfill
                    # self._state = self._ST_DISCONN
                    self._subcription_valid = False
                    self._statelivereconn = self.p.backfill
                    continue

                elif msg == -1102:  # conn broken/restored tickerId maintained
                    # The message may be duplicated
                    if not self._statelivereconn:
                        self._statelivereconn = self.p.backfill
                    continue

                elif msg == -1101:  # conn broken/restored tickerId gone
                    # The message may be duplicated
                    self._subcription_valid = False
                    if not self._statelivereconn:
                        self._statelivereconn = self.p.backfill
                        self.reqdata()  # resubscribe
                    continue

                elif msg == -10225:  # Bust event occurred, current subscription is deactivated.
                    self._subcription_valid = False
                    if not self._statelivereconn:
                        self._statelivereconn = self.p.backfill
                        self.reqdata()  # resubscribe
                    continue

                elif isinstance(msg, integer_types):
                    # Unexpected notification for historical data skip it
                    # May be a "not connected not yet processed"
                    self.put_notification(self.UNKNOWN, msg)
                    continue

                # Process the message according to expected return type
                if not self._statelivereconn:
                    if self._laststatus != self.LIVE:
                        if len(self.qlive) <= 1:  # very short live queue
                            self.put_notification(self.LIVE)

                    if self._usertvol and self._timeframe != bt.TimeFrame.Ticks:
                        ret = self._load_rtvolume(msg)
                    elif self._usertvol and self._timeframe == bt.TimeFrame.Ticks:
                        ret = self._load_rtticks(msg)
                    else:
                        ret = self._load_rtbar(msg)
                    if ret:
                        return True

                    # could not load bar ... go and get new one
                    continue

                # Fall through to processing reconnect - try to backfill
                self._storedmsg[None] = msg  # keep the msg

                # else do a backfill
                if self._laststatus != self.DELAYED:
                    self.put_notification(self.DELAYED)

                dtend = None
                dtend = msg.datetime if self._usertvol else msg.time

                self.qhist = self.ib.reqHistoricalData(
                    contract=self.contract, endDateTime=dtend, 
                    durationStr=self.p.durationStr, barSizeSetting=self.p.barSizeSetting,
                    whatToShow=self.p.what, useRTH=self.p.useRTH,
                    formatDate=self.p.formatDate,keepUpToDate=self.p.keepUpToDate
                    )
                self.qhist.updateEvent += self.onliveupdate

                self.p.fromdate = self.qhist[0].date
                self.p.todate = self.qhist[-1].date
                if isinstance(self.p.fromdate, datetime.date):
                    self.p.fromdate = datetime.datetime.combine(self.p.fromdate, datetime.time())
                if isinstance(self.p.todate, datetime.date):
                    self.p.todate = datetime.datetime.combine(self.p.todate, datetime.time())
                self._state = self._ST_HISTORBACK
                self._statelivereconn = False  # no longer in live
                continue

            elif self._state == self._ST_HISTORBACK:
                if len(self.qhist) > 1:
                    msg = self.qhist.pop(0)
                    if len(self.qhist) == 1:
                        print(f"Final historical data {msg.date}")
                else:
                    if self.p.historical:  # only historical
                        self.put_notification(self.DISCONNECTED)
                        return False  # end of historical

                        # Live is also wished - go for it
                    self._state = self._ST_LIVE
                    continue
                if msg is None:  # Conn broken during historical/backfilling
                    # Situation not managed. Simply bail out
                    self._subcription_valid = False
                    self.put_notification(self.DISCONNECTED)
                    return False  # error management cancelled the queue

                elif msg == -354:  # Data not subscribed
                    self._subcription_valid = False
                    self.put_notification(self.NOTSUBSCRIBED)
                    return False

                elif msg == -420:  # No permissions for the data
                    self._subcription_valid = False
                    self.put_notification(self.NOTSUBSCRIBED)
                    return False

                elif isinstance(msg, integer_types):
                    # Unexpected notification for historical data skip it
                    # May be a "not connected not yet processed"
                    self.put_notification(self.UNKNOWN, msg)
                    continue

                if msg.date is not None:
                    if self._timeframe == bt.TimeFrame.Ticks:
                        if self._load_rtticks(msg, hist=True):
                            return True
                    else:
                        if self._load_rtbar(msg, hist=True):
                            return True  # loading worked

                    # the date is from overlapping historical request
                    continue

                # End of histdata
                if self.p.historical:  # only historical
                    self.put_notification(self.DISCONNECTED)
                    return False  # end of historical

                # Live is also wished - go for it
                self._state = self._ST_LIVE
                continue

            elif self._state == self._ST_FROM:
                if not self.p.backfill_from.next():
                    # additional data source is consumed
                    self._state = self._ST_START
                    continue

                # copy lines of the same name
                for alias in self.lines.getlinealiases():
                    lsrc = getattr(self.p.backfill_from.lines, alias)
                    ldst = getattr(self.lines, alias)

                    ldst[0] = lsrc[0]

                return True

            elif self._state == self._ST_START:
                if not self._st_start():
                    return False

    def _start_finish(self):
        # 重载start_finish方法，ibdata额外增加数据开始日期判断
        super()._start_finish()

        if self.fromdate < date2num(self.constractStartDateUTC):
            print(
                f'From <{self.p.fromdate}> To <{self.constractStartDateUTC}>'
                f'has no constract data, '
                f'data start from {self.constractStartDateUTC}'
                )

    def _st_start(self):
        if self.p.historical:
            self.put_notification(self.DELAYED)
            dtend = ''
            if self.p.todate != '':
                dtend = num2date(self.todate)

            if self._timeframe == bt.TimeFrame.Ticks:
                self.qhist = self.ib.reqHistoricalTicksEx(
                    contract=self.contract, enddate=dtend,
                    what=self.p.what, useRTH=self.p.useRTH, tz=self._tz)
            else:
                self.qhist = self.ib.reqHistoricalData(
                    contract=self.contract, 
                    endDateTime=self.p.todate, 
                    durationStr=self.p.durationStr, 
                    barSizeSetting=self.p.barSizeSetting,
                    whatToShow=self.p.what, 
                    useRTH=self.p.useRTH,
                    formatDate=self.p.formatDate,
                    keepUpToDate=self.p.keepUpToDate
                    )
                self.qhist.updateEvent += self.onliveupdate

            assert len(self.qhist) > 0
            self.p.fromdate = self.qhist[0].date
            self.p.todate = self.qhist[-1].date
            if isinstance(self.p.fromdate, datetime.date):
                self.p.fromdate = datetime.datetime.combine(
                    self.p.fromdate, 
                    datetime.time()
                    )
            if isinstance(self.p.todate, datetime.date):
                self.p.todate = datetime.datetime.combine(
                    self.p.todate, 
                    datetime.time()
                    )
            self._state = self._ST_HISTORBACK
            return True  # continue before

        # Live is requested
        if not self.ib.reconnect(resub=True):
            self.put_notification(self.DISCONNECTED)
            self._state = self._ST_OVER
            return False  # failed - was so

        self._statelivereconn = self.p.backfill_start
        if self.p.backfill_start:
            self.put_notification(self.DELAYED)

        self._state = self._ST_LIVE
        return True  # no return before - implicit continue

    def _load_rtbar(self, rtbar, hist=False):
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
        # A single tick is delivered and is therefore used for the entire set
        # of prices. Ideally the
        # contains open/high/low/close/volume prices
        # Datetime transformation
        dt = date2num(rtvol.datetime)
        if dt < self.lines.datetime[-1] and not self.p.latethrough:
            return False  # cannot deliver earlier than already delivered

        self.lines.datetime[0] = dt

        # Put the tick into the bar
        tick = rtvol.price if rtvol.price else self.lines.close[-1]
        self.lines.open[0] = tick
        self.lines.high[0] = tick
        self.lines.low[0] = tick
        self.lines.close[0] = tick
        self.lines.volume[0] = rtvol.size if rtvol.size else self.lines.volume[-1]
        self.lines.openinterest[0] = 0

        return True

    def _load_rtticks(self, tick, hist=False):

        dt = date2num(tick.datetime if not hist else tick.date)
        if dt < self.lines.datetime[-1] and not self.p.latethrough:
            return False  # cannot deliver earlier than already delivered

        self.lines.datetime[0] = dt

        if tick.dataType == 'RT_TICK_MIDPOINT':
            self.lines.close[0] = tick.midPoint
        elif tick.dataType == 'RT_TICK_BID_ASK':
            self.lines.open[0] = tick.bidPrice
            self.lines.close[0] = tick.askPrice
            self.lines.volume[0] = tick.bidSize
            self.lines.openinterest[0] = tick.askSize
        elif tick.dataType == 'RT_TICK_LAST':
            self.lines.close[0] = tick.price
            self.lines.volume[0] = tick.size

        return True