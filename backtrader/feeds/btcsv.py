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
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import date, datetime, time

from .. import feed
from ..utils import date2num


class BacktraderCSVData(feed.CSVDataBase):
    '''
    Parses a self-defined CSV Data used for testing.

    Specific parameters:

      - ``dataname``: The filename to parse or a file-like object
    '''

    def _loadline(self, linetokens):
        itoken = iter(linetokens)

        dttxt = next(itoken)  # Format is YYYY-MM-DD - skip char 4 and 7
        dt = date(int(dttxt[0:4]), int(dttxt[5:7]), int(dttxt[8:10]))

        if len(linetokens) == 8:
            tmtxt = next(itoken)  # Format if present HH:MM:SS, skip 3 and 6
            tm = time(int(tmtxt[0:2]), int(tmtxt[3:5]), int(tmtxt[6:8]))
        else:
            tm = self.p.sessionend  # end of the session parameter

        self.lines.datetime[0] = date2num(datetime.combine(dt, tm))
        self.lines.open[0] = float(next(itoken))
        self.lines.high[0] = float(next(itoken))
        self.lines.low[0] = float(next(itoken))
        self.lines.close[0] = float(next(itoken))
        self.lines.volume[0] = float(next(itoken))
        self.lines.openinterest[0] = float(next(itoken))

        return True


class BacktraderCSV(feed.CSVFeedBase):
    DataCls = BacktraderCSVData

from backtrader.stores import ibstore_insync
class IBCSVData(feed.CSVDataBase):
    '''
    Parses a self-defined CSV Data used for testing.

    Specific parameters:

      - ``dataname``: The filename to parse or a file-like object
    '''

    params = (
        ('secType', 'STK'),  # usual industry value
        ('exchange', 'SMART'),  # usual industry value
        ('primaryExchange', None),  # native exchange of the contract
        ('right', None),  # Option or Warrant Call('C') or Put('P')
        ('strike', None),  # Future, Option or Warrant strike price
        ('multiplier', None),  # Future, Option or Warrant multiplier
        ('expiry', None),  # Future, Option or Warrant lastTradeDateOrContractMonth date 
        ('tradename', None),  # use a different asset as order target
        ('tradeinfo', None),  # 
        ('datainfo', None),  # 
    )

    #_store = ibstore.IBStore
    _store = ibstore_insync.IBStoreInsync
    
    _ST_FROM, _ST_START, _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(5)

    def __init__(self, **kwargs):
        self.ib = self._store(**kwargs)
        self.precontract = self.parsecontract(self.p.datainfo)
        self.pretradecontract = self.parsecontract(self.p.tradeinfo)
    
    def _loadline(self, linetokens):
        itoken = iter(linetokens)

        dttxt = next(itoken)  # Format is YYYY-MM-DD - skip char 4 and 7
        format_str = '%Y-%m-%d %H:%M:%S%z'
        dt_obj = datetime.strptime(dttxt, format_str)

        self.lines.datetime[0] = date2num(dt_obj)
        self.lines.open[0] = float(next(itoken))
        self.lines.high[0] = float(next(itoken))
        self.lines.low[0] = float(next(itoken))
        self.lines.close[0] = float(next(itoken))
        self.lines.volume[0] = float(next(itoken))
        self.lines.openinterest[0] = float(next(itoken))

        return True
    
    def setenvironment(self, env):
        '''Receives an environment (cerebro) and passes it over to the store it
        belongs to'''
        super(IBCSVData, self).setenvironment(env)
        env.addstore(self.ib)

    CONTRACT_TYPE = [
        'BOND', 'CFD', 'CMDTY', 'CRYPTO', 'CONTFUT', 'CASH', 'IND', 'FUND',
        'STK', 'IOPT', 'FIGI', 'CUSIP', 'ISIN', 'FUT', 'FOP', 'OPT', 'WAR']
    
    def parsecontract(self, dataname):
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
        super(IBCSVData, self).start()

        self.contract = None
        self.contractdetails = None
        self.tradecontract = None
        self.tradecontractdetails = None

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
            dtime = self.ib.reqHeadTimeStamp(contract=self.contract,whatToShow="TRADES", useRTH=1, formatDate=1)
            if isinstance(dtime, datetime) and self.p.historical:
                assert self.p.fromdate >= dtime
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
            cds = self.ib.getContractDetails(self.pretradecontract)
            if cds is not None:
                cdetails = cds[0]
                self.tradecontract = cdetails.contract
                self.tradecontractdetails = cdetails
            else:
                # no contract can be found (or many)
                self.put_notification(self.DISCONNECTED)
                return

        if self._state == self._ST_START:
            pass
            #self._start_finish()  # to finish initialization
            #self._st_start()
            #self._start_updatedate()


class IBCSV(feed.CSVFeedBase):
    DataCls = IBCSVData


class IBCSVOnlyData(feed.CSVDataBase):
    '''
    Parses a self-defined CSV Data used for testing.

    Specific parameters:

      - ``dataname``: The filename to parse or a file-like object
    '''
    
    def _loadline(self, linetokens):
        itoken = iter(linetokens)

        dttxt = next(itoken)  # Format is YYYY-MM-DD - skip char 4 and 7
        try:
            # 尝试按time解析格式
            dt_obj = datetime.strptime(dttxt, '%Y-%m-%d %H:%M:%S-%z')  
        except ValueError:
            # 尝试按date解析格式
            dt_obj = datetime.strptime(dttxt, '%Y-%m-%d')
        self.lines.datetime[0] = date2num(dt_obj)
        self.lines.open[0] = float(next(itoken))
        self.lines.high[0] = float(next(itoken))
        self.lines.low[0] = float(next(itoken))
        self.lines.close[0] = float(next(itoken))
        self.lines.volume[0] = float(next(itoken))
        self.lines.openinterest[0] = float(next(itoken))

        return True


class IBCSVOnly(feed.CSVFeedBase):
    DataCls = IBCSVOnlyData
