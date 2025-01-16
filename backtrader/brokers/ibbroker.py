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

import collections
from copy import copy
from datetime import datetime
import threading
import uuid

from backtrader.feed import DataBase
from backtrader import (date2num, BrokerBase, Order)
from backtrader.utils.py3 import (string_types, 
    integer_types, with_metaclass, queue, MAXFLOAT)
from backtrader.metabase import MetaParams
from backtrader.commissions.ibcommission import IBCommInfo
from backtrader.orders.iborder import IBOrder
from backtrader.position import Position
from backtrader.stores import ibstore_insync

class MetaSingletonIBBroker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaSingletonIBBroker, cls).__init__(name, bases, dct)
        #ibstore.IBStore.BrokerCls = cls
        ibstore_insync.IBStoreInsync.BrokerCls = cls
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (
                super(MetaSingletonIBBroker, cls).__call__(*args, **kwargs))

        return cls._singleton

class IBBroker(with_metaclass(MetaSingletonIBBroker, BrokerBase)):
    '''Broker implementation for Interactive Brokers.

    This class maps the orders/positions from Interactive Brokers to the
    internal API of ``backtrader``.

    Notes:

      - ``tradeid`` is not really supported, because the profit and loss are
        taken directly from IB. Because (as expected) calculates it in FIFO
        manner, the pnl is not accurate for the tradeid.

      - Position

        If there is an open position for an asset at the beginning of
        operaitons or orders given by other means change a position, the trades
        calculated in the ``Strategy`` in cerebro will not reflect the reality.

        To avoid this, this broker would have to do its own position
        management which would also allow tradeid with multiple ids (profit and
        loss would also be calculated locally), but could be considered to be
        defeating the purpose of working with a live broker
    '''
    params = (
        ('cash', 10000.0),
        ('checksubmit', True), 
        ('filler', None),
        # slippage options 滑点
        ('slip_perc', 0.0),
        ('slip_fixed', 0.0),
        ('slip_open', False),
        ('slip_match', True),
        ('slip_limit', True),
        ('slip_out', False),
        ('coc', False),
        ('coo', False),
        ('int2pnl', True),
        ('shortcash', True),
        ('fundstartval', 100.0),
        ('fundmode', False),
        ('runmode', None),
    )

    def __init__(self, **kwargs):
        super(IBBroker, self).__init__()
        self._userhist = []
        self._fundhist = []
        # share_value, net asset value
        self._fhistlast = [float('NaN'), float('NaN')]
        self.ib = ibstore_insync.IBStoreInsync()
        if self.p.runmode:
            self.runmode = self.p.runmode
        else:
            self.runmode = self.ib.runmode

    def init(self):
        '''
        init会在super().__init__中调用,
        因此init的执行是在__init__中的第一句被调用,__init__中初始化的代码都init()后执行

        init会被重复调用,在init和broker.start()中都会被调用
        '''
        super(IBBroker, self).init()
        self.startingcash = self.cash = self.validcash = self.p.cash
        self.startingvalue = self.value = 0.0

        self._value = self.cash
        self._valuemkt = 0.0  # no open position

        self._valuelever = 0.0  # no open position
        self._valuemktlever = 0.0  # no open position

        self.orders = list()  # will only be appending
        self.pending = collections.deque()  # popleft and append(right)
        self._toactivate = collections.deque()  # to activate in next cycle

        self.positions = collections.defaultdict(Position)
        self.d_credit = collections.defaultdict(float)  # credit per data
        self.notifs = collections.deque()
        
        self.submitted = collections.deque()

        # to keep dependent orders if needed
        self._pchildren = collections.defaultdict(collections.deque)

        self._ocos = dict()
        self._ocol = collections.defaultdict(list) 

        self._fundval = self.p.fundstartval
        self._fundshares = self.p.cash / self._fundval
        self._cash_addition = collections.deque()

        self._lock_orders = threading.Lock()  # control access
        self.orderbyid = dict()  # orders by order id
        self.executions = dict()  # notified executions
        self.ordstatus = collections.defaultdict(dict)
        self.tonotify = collections.deque()  # hold oids to be notified

    def start(self):
        super().init()
        if not self.checkorder:
            for data in self.ib.datas:
                if self.positions[data] is None:
                    position = self.ib.getposition(data=data, clone=True)
                    self.positions[data] = Position()
                    self.positions[data].price = \
                        position.avgCost/abs(position.position)
                    self.positions[data].size = position.position

    @property
    def checkorder(self):
        #True: 本地检查，事件驱动
        #False: 平台检查，平台回调驱动，本地仅保存状态
        return self.runmode == 'backtest'
        
    def get_notification(self):
        try:
            return self.notifs.popleft()
        except IndexError:
            pass

        return None  
    
    def set_fundmode(self, fundmode, fundstartval=None):
        '''Set the actual fundmode (True or False)

        If the argument fundstartval is not ``None``, it will used
        '''
        self.p.fundmode = fundmode
        if fundstartval is not None:
            self.set_fundstartval(fundstartval)

    def get_fundmode(self):
        '''Returns the actual fundmode (True or False)'''
        return self.p.fundmode

    fundmode = property(get_fundmode, set_fundmode)

    def set_fundstartval(self, fundstartval):
        '''Set the starting value of the fund-like performance tracker'''
        self.p.fundstartval = fundstartval

    def set_int2pnl(self, int2pnl):
        '''Configure assignment of interest to profit and loss'''
        self.p.int2pnl = int2pnl

    def set_coc(self, coc):
        '''Configure the Cheat-On-Close method to buy the close on order bar'''
        self.p.coc = coc

    def set_coo(self, coo):
        '''Configure the Cheat-On-Open method to buy the close on order bar'''
        self.p.coo = coo

    def set_shortcash(self, shortcash):
        '''Configure the shortcash parameters'''
        self.p.shortcash = shortcash

    def set_slippage_perc(self, perc,
                          slip_open=True, slip_limit=True,
                          slip_match=True, slip_out=False):
        '''Configure slippage to be percentage based'''
        self.p.slip_perc = perc
        self.p.slip_fixed = 0.0
        self.p.slip_open = slip_open
        self.p.slip_limit = slip_limit
        self.p.slip_match = slip_match
        self.p.slip_out = slip_out

    def set_slippage_fixed(self, fixed,
                           slip_open=True, slip_limit=True,
                           slip_match=True, slip_out=False):
        '''Configure slippage to be fixed points based'''
        self.p.slip_perc = 0.0
        self.p.slip_fixed = fixed
        self.p.slip_open = slip_open
        self.p.slip_limit = slip_limit
        self.p.slip_match = slip_match
        self.p.slip_out = slip_out

    def set_filler(self, filler):
        '''Sets a volume filler for volume filling execution'''
        self.p.filler = filler

    def set_checksubmit(self, checksubmit):
        '''Sets the checksubmit parameter'''
        self.p.checksubmit = checksubmit

    def get_cash(self):
        # This call cannot block if no answer is available from ib
        if self.checkorder:
            return self.cash
        else:
            self.cash = self.ib.get_acc_cash()
            return self.cash
    getcash = get_cash

    def get_validcash(self):
        # This call cannot block if no answer is available from ib
        if self.checkorder:
            return self.validcash
        else:
            self.validcash = self.ib.get_acc_validcash()
            return self.self.validcash

    def set_cash(self, cash):
        '''Sets the cash parameter (alias: ``setcash``)'''
        if self.checkorder:
            self.startingcash = self.cash = self.p.cash = cash
            self._value = cash

    setcash = set_cash

    def add_cash(self, cash):
        '''Add/Remove cash to the system (use a negative value to remove)'''
        self._cash_addition.append(cash)

    def get_fundshares(self):
        '''Returns the current number of shares in the fund-like mode'''
        return self._fundshares

    fundshares = property(get_fundshares)

    def get_fundvalue(self):
        '''Returns the Fund-like share value'''
        return self._fundval

    fundvalue = property(get_fundvalue)

    def cancel(self, order, bracket=False):
        if self.checkorder:
            try:
                self.pending.remove(order)
            except ValueError:
                # If the list didn't have the element we didn't cancel anything
                return False

            order.cancel()
            self.notify(order)
            self._ococheck(order)
            if not bracket:
                self._bracketize(order, cancel=True)
            return True
        else:
            try:
                o = self.orderbyid[order.orderId]
            except (ValueError, KeyError):
                return  # not found ... not cancellable

            if order.status == Order.Cancelled:  # already cancelled
                return

            self.ib.cancelOrder(order.orderId)

    def get_value(self, datas=None, mkt=False, lever=False):
        '''Returns the portfolio value of the given datas (if datas is ``None``, then
        the total portfolio value will be returned (alias: ``getvalue``)
        '''
        if self.checkorder:
            if datas is None:
                if mkt:
                    return self._valuemkt if not lever else self._valuemktlever

                return self._value if not lever else self._valuelever

            return self._get_value(datas=datas, lever=lever)
        else:
            self.value = self.ib.get_acc_value()
            return self.value
    getvalue = get_value

    def _get_value(self, datas=None, lever=False):
        pos_value = 0.0
        pos_value_unlever = 0.0
        unrealized = 0.0

        while self._cash_addition:
            c = self._cash_addition.popleft()
            self._fundshares += c / self._fundval
            self.cash += c

        for data in datas or self.positions:
            comminfo = self.getcommissioninfo(data)
            position = self.positions[data]
            # use valuesize:  returns raw value, rather than negative adj val
            if not self.p.shortcash:
                dvalue = comminfo.getvalue(position, data.close[0])
            else:
                dvalue = comminfo.getvaluesize(position.size, data.close[0])

            dunrealized = comminfo.profitandloss(position.size, position.price,
                                                 data.close[0])
            if datas and len(datas) == 1:
                if lever and dvalue > 0:
                    dvalue -= dunrealized
                    return (dvalue / comminfo.get_leverage()) + dunrealized
                return dvalue  # raw data value requested, short selling is neg

            if not self.p.shortcash:
                dvalue = abs(dvalue)  # short selling adds value in this case

            pos_value += dvalue
            unrealized += dunrealized

            if dvalue > 0:  # long position - unlever
                dvalue -= dunrealized
                pos_value_unlever += (dvalue / comminfo.get_leverage())
                pos_value_unlever += dunrealized
            else:
                pos_value_unlever += dvalue

        if not self._fundhist:
            self._value = v = self.cash + pos_value_unlever
            self._fundval = self._value / self._fundshares  # update fundvalue
        else:
            # Try to fetch a value
            fval, fvalue = self._process_fund_history()

            self._value = fvalue
            self.cash = fvalue - pos_value_unlever
            self._fundval = fval
            self._fundshares = fvalue / fval
            lev = pos_value / (pos_value_unlever or 1.0)

            # update the calculated values above to the historical values
            pos_value_unlever = fvalue
            pos_value = fvalue * lev

        self._valuemkt = pos_value_unlever

        self._valuelever = self.cash + pos_value
        self._valuemktlever = pos_value

        self._leverage = pos_value / (pos_value_unlever or 1.0)
        self._unrealized = unrealized

        return self._value if not lever else self._valuelever

    def getposition(self, data, clone=True):
        if self.checkorder:
            return self.positions[data]
        else:
            return self.positions[data]


    def orderstatus(self, order):
        try:
            o = self.orders.index(order)
        except ValueError:
            o = order

        return o.status

    def _take_children(self, order):
        oref = order.ref
        pref = getattr(order.parent, 'ref', oref)  # parent ref or self

        if oref != pref:
            if pref not in self._pchildren:
                order.reject()  # parent not there - may have been rejected
                self.notify(order)  # reject child, notify
                return None

        return pref

    def submit(self, order, check=True):
        pref = self._take_children(order)
        if pref is None:  # order has not been taken
            return order

        pc = self._pchildren[pref]
        pc.append(order)  # store in parent/children queue

        if order.transmit:  # if single order, sent and queue cleared
            # if parent-child, the parent will be sent, the other kept
            rets = [self.transmit(x, check=check) for x in pc]
            return rets[-1]  # last one is the one triggering transmission

        return order

    def transmit(self, order, check=True):
        if check and self.p.checksubmit:
            order.submit()
            self.submitted.append(order)
            self.orders.append(order)
            self.notify(order)
        else:
            self.submit_accept(order)

        return order

    def check_submitted(self):
        cash = self.cash
        positions = dict()

        while self.submitted:
            order = self.submitted.popleft()

            if self._take_children(order) is None:  # children not taken
                continue

            comminfo = self.getcommissioninfo(order.data)

            position = positions.setdefault(
                order.data, self.positions[order.data].clone())

            # pseudo-execute the order to get the remaining cash after exec
            cash = self._execute(order, cash=cash, position=position)

            if cash >= 0.0:
                self.submit_accept(order)
                continue

            order.margin()
            self.notify(order)
            self._ococheck(order)
            self._bracketize(order, cancel=True)

    def submit_accept(self, order):
        order.pannotated = None
        order.submit()
        order.accept()
        self.pending.append(order)
        self.notify(order)

    def _bracketize(self, order, cancel=False):
        oref = order.ref
        pref = getattr(order.parent, 'ref', oref)
        parent = oref == pref

        pc = self._pchildren[pref]  # defdict - guaranteed
        if cancel or not parent:  # cancel left or child exec -> cancel other
            while pc:
                self.cancel(pc.popleft(), bracket=True)  # idempotent

            del self._pchildren[pref]  # defdict guaranteed

        else:  # not cancel -> parent exec'd
            pc.popleft()  # remove parent
            for o in pc:  # activate childnre
                self._toactivate.append(o)

    def _ococheck(self, order):
        # ocoref = self._ocos[order.ref] or order.ref  # a parent or self
        parentref = self._ocos[order.ref]
        ocoref = self._ocos.get(parentref, None)
        ocol = self._ocol.pop(ocoref, None)
        if ocol:
            for i in range(len(self.pending) - 1, -1, -1):
                o = self.pending[i]
                if o is not None and o.ref in ocol:
                    del self.pending[i]
                    o.cancel()
                    self.notify(o)

    def _ocoize(self, order, oco):
        oref = order.ref
        if oco is None:
            self._ocos[oref] = oref  # current order is parent
            self._ocol[oref].append(oref)  # create ocogroup
        else:
            ocoref = self._ocos[oco.ref]  # ref to group leader
            self._ocos[oref] = ocoref  # ref to group leader
            self._ocol[ocoref].append(oref)  # add to group

    def _makeorder(self, action, owner, data, size,**kwargs):
        '''
        开仓必须使用BKT bracketOrder 套利单
        平仓必须使用LMT limitOrder 限价单
        '''
        order = IBOrder(action=action, 
                    owner=owner, 
                    data=data, 
                    size=size,
                    **kwargs)

        order.addcomminfo(self.getcommissioninfo(data))
        return order
            
    def buy(self, owner, data, size, **kwargs):  
        action = kwargs.pop('action', 'BUY')
        if self.checkorder:
            order = IBOrder(owner=owner, data=data, size=size, action=action, **kwargs)
            oco = kwargs.get('oco', None)
            order.addinfo(**kwargs)
            self._ocoize(order, oco)
            return self.submit(order)
        else:
            order = self._makeorder('BUY', owner, data, size, **kwargs)
            return self.ib.placeOrder(order.data.tradecontract, order)
  

    def sell(self, owner, data, size, **kwargs):
        action = kwargs.pop('action', 'SELL')
        if self.checkorder:
            order = IBOrder(owner=owner, data=data, size=size, action=action, **kwargs)
            oco = kwargs.get('oco', None)      
            order.addinfo(**kwargs)
            self._ocoize(order, oco)
            return self.submit(order)
        else:
            order = self._makeorder('SELL', owner, data, size,**kwargs)
            return self.ib.placeOrder(order.data.tradecontract, order)
    
    
    def _execute(self, order, ago=None, price=None, cash=None, position=None,
                 dtcoc=None):
        # ago = None is used a flag for pseudo execution
        if ago is not None and price is None:
            return  # no psuedo exec no price - no execution

        if self.p.filler is None or ago is None:
            # Order gets full size or pseudo-execution
            size = order.executed.remsize
        else:
            # Execution depends on volume filler
            size = self.p.filler(order, price, ago)
            if not order.isbuy():
                size = -size

        # Get comminfo object for the data
        comminfo = self.getcommissioninfo(order.data)

        # Check if something has to be compensated
        if order.data._compensate is not None:
            data = order.data._compensate
            cinfocomp = self.getcommissioninfo(data)  # for actual commission
        else:
            data = order.data
            cinfocomp = comminfo

        # Adjust position with operation size
        if ago is not None:
            # Real execution with date
            position = self.positions[data]
            pprice_orig = position.price

            psize, pprice, opened, closed = position.pseudoupdate(size, price)

            # if part/all of a position has been closed, then there has been
            # a profitandloss ... record it
            pnl = comminfo.profitandloss(-closed, pprice_orig, price)
            cash = self.cash
        else:
            pnl = 0
            if not self.p.coo:
                price = pprice_orig = order.created.price
            else:
                # When doing cheat on open, the price to be considered for a
                # market order is the opening price and not the default closing
                # price with which the order was created
                if order.exectype == Order.Market:
                    price = pprice_orig = order.data.open[0]
                else:
                    price = pprice_orig = order.created.price

            psize, pprice, opened, closed = position.update(size, price)

        # "Closing" totally or partially is possible. Cash may be re-injected
        if closed:
            # Adjust to returned value for closed items & acquired opened items
            if self.p.shortcash:
                closedvalue = comminfo.getvaluesize(-closed, pprice_orig)
            else:
                closedvalue = comminfo.getoperationcost(closed, pprice_orig)

            closecash = closedvalue
            if closedvalue > 0:  # long position closed
                closecash /= comminfo.get_leverage()  # inc cash with lever

            cash += closecash + pnl * comminfo.stocklike
            # Calculate and substract commission
            closedcomm = comminfo.getcommission(closed, price)
            cash -= closedcomm

            if ago is not None:
                # Cashadjust closed contracts: prev close vs exec price
                # The operation can inject or take cash out
                cash += comminfo.cashadjust(-closed,
                                            position.adjbase,
                                            price)

                # Update system cash
                self.cash = cash
        else:
            closedvalue = closedcomm = 0.0

        popened = opened
        if opened:
            if self.p.shortcash:
                openedvalue = comminfo.getvaluesize(opened, price)
            else:
                openedvalue = comminfo.getoperationcost(opened, price)

            opencash = openedvalue
            if openedvalue > 0:  # long position being opened
                opencash /= comminfo.get_leverage()  # dec cash with level

            cash -= opencash  # original behavior

            openedcomm = cinfocomp.getcommission(opened, price)
            cash -= openedcomm

            if cash < 0.0:
                # execution is not possible - nullify
                opened = 0
                openedvalue = openedcomm = 0.0

            elif ago is not None:  # real execution
                if abs(psize) > abs(opened):
                    # some futures were opened - adjust the cash of the
                    # previously existing futures to the operation price and
                    # use that as new adjustment base, because it already is
                    # for the new futures At the end of the cycle the
                    # adjustment to the close price will be done for all open
                    # futures from a common base price with regards to the
                    # close price
                    adjsize = psize - opened
                    cash += comminfo.cashadjust(adjsize,
                                                position.adjbase, price)

                # record adjust price base for end of bar cash adjustment
                position.adjbase = price

                # update system cash - checking if opened is still != 0
                self.cash = cash
        else:
            openedvalue = openedcomm = 0.0

        if ago is None:
            # return cash from pseudo-execution
            return cash

        execsize = closed + opened

        if execsize:
            # Confimrm the operation to the comminfo object
            comminfo.confirmexec(execsize, price)

            # do a real position update if something was executed
            position.update(execsize, price, data.datetime.datetime())

            if closed and self.p.int2pnl:  # Assign accumulated interest data
                closedcomm += self.d_credit.pop(data, 0.0)

            # Execute and notify the order
            order.execute(dtcoc or data.datetime[ago],
                          execsize, price,
                          closed, closedvalue, closedcomm,
                          opened, openedvalue, openedcomm,
                          comminfo.margin, pnl,
                          psize, pprice)

            order.addcomminfo(comminfo)

            self.notify(order)
            self._ococheck(order)

        if popened and not opened:
            # opened was not executed - not enough cash
            order.margin()
            self.notify(order)
            self._ococheck(order)
            self._bracketize(order, cancel=True)

    def notify(self, order):
        self.notifs.append(order.clone())

    
    def _try_exec_historical(self, order):
        self._execute(order, ago=0, price=order.created.price)

    def _try_exec_market(self, order, popen, phigh, plow):
        ago = 0
        if self.p.coc and order.info.get('coc', True):
            dtcoc = order.created.dt
            exprice = order.created.pclose
        else:
            if not self.p.coo and order.data.datetime[0] <= order.created.dt:
                return    # can only execute after creation time

            dtcoc = None
            exprice = popen

        if order.isbuy():
            p = self._slip_up(phigh, exprice, doslip=self.p.slip_open)
        else:
            p = self._slip_down(plow, exprice, doslip=self.p.slip_open)

        self._execute(order, ago=0, price=p, dtcoc=dtcoc)

    def _try_exec_close(self, order, pclose):
        # pannotated allows to keep track of the closing bar if there is no
        # information which lets us know that the current bar is the closing
        # bar (like matching end of session bar)
        # The actual matching will be done one bar afterwards but using the
        # information from the actual closing bar

        dt0 = order.data.datetime[0]
        # don't use "len" -> in replay the close can be reached with same len
        if dt0 > order.created.dt:  # can only execute after creation time
            # or (self.p.eosbar and dt0 == order.dteos):
            if dt0 >= order.dteos:
                # past the end of session or right at it and eosbar is True
                if order.pannotated and dt0 > order.dteos:
                    ago = -1
                    execprice = order.pannotated
                else:
                    ago = 0
                    execprice = pclose

                self._execute(order, ago=ago, price=execprice)
                return

        # If no exexcution has taken place ... annotate the closing price
        order.pannotated = pclose

    def _try_exec_limit(self, order, popen, phigh, plow, plimit):
        if order.isbuy():
            if plimit >= popen:
                # open smaller/equal than requested - buy cheaper
                pmax = min(phigh, plimit)
                p = self._slip_up(pmax, popen, doslip=self.p.slip_open,
                                  lim=True)
                self._execute(order, ago=0, price=p)
            elif plimit >= plow:
                # day low below req price ... match limit price
                self._execute(order, ago=0, price=plimit)

        else:  # Sell
            if plimit <= popen:
                # open greater/equal than requested - sell more expensive
                pmin = max(plow, plimit)
                p = self._slip_down(plimit, popen, doslip=self.p.slip_open,
                                    lim=True)
                self._execute(order, ago=0, price=p)
            elif plimit <= phigh:
                # day high above req price ... match limit price
                self._execute(order, ago=0, price=plimit)

    def _try_exec_stop(self, order, popen, phigh, plow, pcreated, pclose):
        if order.isbuy():
            if popen >= pcreated:
                # price penetrated with an open gap - use open
                p = self._slip_up(phigh, popen, doslip=self.p.slip_open)
                self._execute(order, ago=0, price=p)
            elif phigh >= pcreated:
                # price penetrated during the session - use trigger price
                p = self._slip_up(phigh, pcreated)
                self._execute(order, ago=0, price=p)

        else:  # Sell
            if popen <= pcreated:
                # price penetrated with an open gap - use open
                p = self._slip_down(plow, popen, doslip=self.p.slip_open)
                self._execute(order, ago=0, price=p)
            elif plow <= pcreated:
                # price penetrated during the session - use trigger price
                p = self._slip_down(plow, pcreated)
                self._execute(order, ago=0, price=p)

        # not (completely) executed and trailing stop
        if order.alive() and order.exectype == Order.StopTrail:
            order.trailadjust(pclose)

    def _try_exec_stoplimit(self, order,
                            popen, phigh, plow, pclose,
                            pcreated, plimit):
        if order.isbuy():
            if popen >= pcreated:
                order.triggered = True
                self._try_exec_limit(order, popen, phigh, plow, plimit)

            elif phigh >= pcreated:
                # price penetrated upwards during the session
                order.triggered = True
                # can calculate execution for a few cases - datetime is fixed
                if popen > pclose:
                    if plimit >= pcreated:  # limit above stop trigger
                        p = self._slip_up(phigh, pcreated, lim=True)
                        self._execute(order, ago=0, price=p)
                    elif plimit >= pclose:
                        self._execute(order, ago=0, price=plimit)
                else:  # popen < pclose
                    if plimit >= pcreated:
                        p = self._slip_up(phigh, pcreated, lim=True)
                        self._execute(order, ago=0, price=p)
        else:  # Sell
            if popen <= pcreated:
                # price penetrated downwards with an open gap
                order.triggered = True
                self._try_exec_limit(order, popen, phigh, plow, plimit)

            elif plow <= pcreated:
                # price penetrated downwards during the session
                order.triggered = True
                # can calculate execution for a few cases - datetime is fixed
                if popen <= pclose:
                    if plimit <= pcreated:
                        p = self._slip_down(plow, pcreated, lim=True)
                        self._execute(order, ago=0, price=p)
                    elif plimit <= pclose:
                        self._execute(order, ago=0, price=plimit)
                else:
                    # popen > pclose
                    if plimit <= pcreated:
                        p = self._slip_down(plow, pcreated, lim=True)
                        self._execute(order, ago=0, price=p)

        # not (completely) executed and trailing stop
        if order.alive() and order.exectype == Order.StopTrailLimit:
            order.trailadjust(pclose)

    def _slip_up(self, pmax, price, doslip=True, lim=False):
        if not doslip:
            return price

        slip_perc = self.p.slip_perc
        slip_fixed = self.p.slip_fixed
        if slip_perc:
            pslip = price * (1 + slip_perc)
        elif slip_fixed:
            pslip = price + slip_fixed
        else:
            return price

        if pslip <= pmax:  # slipping can return price
            return pslip
        elif self.p.slip_match or (lim and self.p.slip_limit):
            if not self.p.slip_out:
                return pmax

            return pslip  # non existent price

        return None  # no price can be returned

    def _slip_down(self, pmin, price, doslip=True, lim=False):
        if not doslip:
            return price

        slip_perc = self.p.slip_perc
        slip_fixed = self.p.slip_fixed
        if slip_perc:
            pslip = price * (1 - slip_perc)
        elif slip_fixed:
            pslip = price - slip_fixed
        else:
            return price

        if pslip >= pmin:  # slipping can return price
            return pslip
        elif self.p.slip_match or (lim and self.p.slip_limit):
            if not self.p.slip_out:
                return pmin

            return pslip  # non existent price

        return None  # no price can be returned

    def _try_exec(self, order):
        data = order.data

        popen = getattr(data, 'tick_open', None)
        if popen is None:
            popen = data.open[0]
        phigh = getattr(data, 'tick_high', None)
        if phigh is None:
            phigh = data.high[0]
        plow = getattr(data, 'tick_low', None)
        if plow is None:
            plow = data.low[0]
        pclose = getattr(data, 'tick_close', None)
        if pclose is None:
            pclose = data.close[0]

        pcreated = order.created.price
        plimit = order.created.pricelimit

        if order.exectype == Order.Market:
            self._try_exec_market(order, popen, phigh, plow)

        elif order.exectype == Order.Close:
            self._try_exec_close(order, pclose)

        elif order.exectype == Order.Limit:
            self._try_exec_limit(order, popen, phigh, plow, pcreated)

        elif (order.triggered and
              order.exectype in [Order.StopLimit, Order.StopTrailLimit]):
            self._try_exec_limit(order, popen, phigh, plow, plimit)

        elif order.exectype in [Order.Stop, Order.StopTrail]:
            self._try_exec_stop(order, popen, phigh, plow, pcreated, pclose)

        elif order.exectype in [Order.StopLimit, Order.StopTrailLimit]:
            self._try_exec_stoplimit(order,
                                     popen, phigh, plow, pclose,
                                     pcreated, plimit)

        elif order.exectype == Order.Historical:
            self._try_exec_historical(order)

    def _process_fund_history(self):
        fhist = self._fundhist  # [last element, iterator]
        f, funds = fhist
        if not f:
            return self._fhistlast

        dt = f[0]  # date/datetime instance
        if isinstance(dt, string_types):
            dtfmt = '%Y-%m-%d'
            if 'T' in dt:
                dtfmt += 'T%H:%M:%S'
                if '.' in dt:
                    dtfmt += '.%f'
            dt = datetime.datetime.strptime(dt, dtfmt)
            f[0] = dt  # update value

        elif isinstance(dt, datetime.datetime):
            pass
        elif isinstance(dt, datetime.date):
            dt = datetime.datetime(year=dt.year, month=dt.month, day=dt.day)
            f[0] = dt  # Update the value

        # Synchronization with the strategy is not possible because the broker
        # is called before the strategy advances. The 2 lines below would do it
        # if possible
        # st0 = self.cerebro.runningstrats[0]
        # if dt <= st0.datetime.datetime():
        if dt <= self.cerebro._dtmaster:
            self._fhistlast = f[1:]
            fhist[0] = list(next(funds, []))

        return self._fhistlast

    def _process_order_history(self):
        for uhist in self._userhist:
            uhorder, uhorders, uhnotify = uhist
            while uhorder is not None:
                uhorder = list(uhorder)  # to support assignment (if tuple)
                try:
                    dataidx = uhorder[3]  # 2nd field
                except IndexError:
                    dataidx = None  # Field not present, use default

                if dataidx is None:
                    d = self.cerebro.datas[0]
                elif isinstance(dataidx, integer_types):
                    d = self.cerebro.datas[dataidx]
                else:  # assume string
                    d = self.cerebro.datasbyname[dataidx]

                if not len(d):
                    break  # may start later as oter data feeds

                dt = uhorder[0]  # date/datetime instance
                if isinstance(dt, string_types):
                    dtfmt = '%Y-%m-%d'
                    if 'T' in dt:
                        dtfmt += 'T%H:%M:%S'
                        if '.' in dt:
                            dtfmt += '.%f'
                    dt = datetime.datetime.strptime(dt, dtfmt)
                    uhorder[0] = dt
                elif isinstance(dt, datetime.datetime):
                    pass
                elif isinstance(dt, datetime.date):
                    dt = datetime.datetime(year=dt.year,
                                           month=dt.month,
                                           day=dt.day)
                    uhorder[0] = dt

                if dt > d.datetime.datetime():
                    break  # cannot execute yet 1st in queue, stop processing

                size = uhorder[1]
                price = uhorder[2]
                owner = self.cerebro.runningstrats[0]
                if size > 0:
                    o = self.buy(owner=owner, data=d,
                                 size=size, price=price,
                                 exectype=Order.Historical,
                                 histnotify=uhnotify,
                                 _checksubmit=False)

                elif size < 0:
                    o = self.sell(owner=owner, data=d,
                                  size=abs(size), price=price,
                                  exectype=Order.Historical,
                                  histnotify=uhnotify,
                                  _checksubmit=False)

                # update to next potential order
                uhist[0] = uhorder = next(uhorders, None)

    def next(self):
        if self.checkorder:
            while self._toactivate:
                self._toactivate.popleft().activate()

            if self.p.checksubmit:
                self.check_submitted()

            # Discount any cash for positions hold
            credit = 0.0
            for data, pos in self.positions.items():
                if pos:
                    comminfo = self.getcommissioninfo(data)
                    dt0 = data.datetime.datetime()
                    dcredit = comminfo.get_credit_interest(data, pos, dt0)
                    self.d_credit[data] += dcredit
                    credit += dcredit
                    pos.datetime = dt0  # mark last credit operation

            self.cash -= credit

            self._process_order_history()

            # Iterate once over all elements of the pending queue
            self.pending.append(None)
            while True:
                order = self.pending.popleft()
                if order is None:
                    break

                if order.expire():
                    self.notify(order)
                    self._ococheck(order)
                    self._bracketize(order, cancel=True)

                elif not order.active():     #只针对子订单
                    self.pending.append(order)  # cannot yet be processed

                else:
                    self._try_exec(order)

                    if order.alive():
                        self.pending.append(order)

                    elif order.status == Order.Completed:
                        # a bracket parent order may have been executed
                        self._bracketize(order)

            # Operations have been executed ... adjust cash end of bar
            for data, pos in self.positions.items():
                # futures change cash every bar
                if pos:
                    comminfo = self.getcommissioninfo(data)
                    self.cash += comminfo.cashadjust(pos.size,
                                                    pos.adjbase,
                                                    data.close[0])
                
                    # record the last adjustment price
                    pos.adjbase = data.close[0]

            self._get_value()  # update value

    def push_orderstatus(self, msg):
        # Cancelled and Submitted with Filled = 0 can be pushed immediately
        try:
            order = self.orderbyid[msg.orderId]
        except KeyError:
            return  # not found, it was not an order

        if msg.status == self.SUBMITTED and msg.filled == 0:
            if order.status == order.Accepted:  # duplicate detection
                return

            order.accept(self)
            self.notify(order)

        elif msg.status == self.CANCELLED:
            # duplicate detection
            if order.status in [order.Cancelled, order.Expired]:
                return

            if order._willexpire:
                # An openOrder has been seen with PendingCancel/Cancelled
                # and this happens when an order expires
                order.expire()
            else:
                # Pure user cancellation happens without an openOrder
                order.cancel()
            self.notify(order)

        elif msg.status == self.PENDINGCANCEL:
            # In theory this message should not be seen according to the docs,
            # but other messages like PENDINGSUBMIT which are similarly
            # described in the docs have been received in the demo
            if order.status == order.Cancelled:  # duplicate detection
                return

            # We do nothing because the situation is handled with the 202 error
            # code if no orderStatus with CANCELLED is seen
            # order.cancel()
            # self.notify(order)

        elif msg.status == self.INACTIVE:
            # This is a tricky one, because the instances seen have led to
            # order rejection in the demo, but according to the docs there may
            # be a number of reasons and it seems like it could be reactivated
            if order.status == order.Rejected:  # duplicate detection
                return

            order.reject(self)
            self.notify(order)

        elif msg.status in [self.SUBMITTED, self.FILLED]:
            # These two are kept inside the order until execdetails and
            # commission are all in place - commission is the last to come
            self.ordstatus[msg.orderId][msg.filled] = msg

        elif msg.status in [self.PENDINGSUBMIT, self.PRESUBMITTED]:
            # According to the docs, these statuses can only be set by the
            # programmer but the demo account sent it back at random times with
            # "filled"
            if msg.filled:
                self.ordstatus[msg.orderId][msg.filled] = msg
        else:  # Unknown status ...
            pass

    def push_execution(self, ex):
        self.executions[ex.execId] = ex

    def push_commissionreport(self, cr):
        with self._lock_orders:
            try:
                ex = self.executions.pop(cr.execId)
                oid = ex.orderId
                order = self.orderbyid[oid]
                ostatus = self.ordstatus[oid].pop(ex.cumQty)
                
                position = self.getposition(contract=order.data, clone=False)
                pprice_orig = position.price
                size = ex.shares if ex.side[0] == 'B' else -ex.shares
                price = ex.price
                # use pseudoupdate and let the updateportfolio do the real update?
                psize, pprice, opened, closed = position.update(float(size), price)
                
                # split commission between closed and opened
                comm = cr.commission
                closedcomm = comm *  float(closed) / float(size)
                openedcomm = comm - closedcomm
                
                comminfo = order.comminfo
                closedvalue = comminfo.getoperationcost(closed, pprice_orig)
                openedvalue = comminfo.getoperationcost(opened, price)
                
                # default in m_pnl is MAXFLOAT
                pnl = cr.realizedPNL if closed else 0.0
				
				# The internal broker calc should yield the same result
				# pnl = comminfo.profitandloss(-closed, pprice_orig, price)
				
				# Use the actual time provided by the execution object
				# The report from TWS is in actual local time, not the data's tz
				#dt = date2num(datetime.strptime(ex.time, '%Y%m%d  %H:%M:%S'))
                dt_array = [] if ex.time == None else ex.time.split(" ")
                if dt_array and len(dt_array) > 1:
                    dt_array.pop()
                    ex_time = " ".join(dt_array)
                    dt = date2num(datetime.strptime(ex_time, '%Y%m%d %H:%M:%S'))
                else:
                    dt = date2num(datetime.strptime(ex.time, '%Y%m%d %H:%M:%S %A'))															 
					
				# Need to simulate a margin, but it plays no role, because it is
				# controlled by a real broker. Let's set the price of the item
                margin = order.data.close[0]
                
                order.execute(dt, float(size),  price,
                          float(closed), closedvalue, closedcomm,
                          opened, openedvalue, openedcomm,
                          margin, pnl,
                          float(psize), pprice)
                
                if ostatus.status == self.FILLED:
                    order.completed()
                    self.ordstatus.pop(oid)  # nothing left to be reported
                else:
                    order.partial()
                
                if oid not in self.tonotify:  # Lock needed
                    self.tonotify.append(oid)
            except Exception as e:
                self.ib._logger.exception(f"Exception: {e}")						  

    def push_portupdate(self):
        # If the IBStore receives a Portfolio update, then this method will be
        # indicated. If the execution of an order is split in serveral lots,
        # updatePortfolio messages will be intermixed, which is used as a
        # signal to indicate that the strategy can be notified
        with self._lock_orders:
            while self.tonotify:
                oid = self.tonotify.popleft()
                order = self.orderbyid[oid]
                self.notify(order)

    def push_ordererror(self, msg):
        with self._lock_orders:
            try:
                order = self.orderbyid[msg.id]
            except (KeyError, AttributeError):
                return  # no order or no id in error

            if msg.errorCode == 202:
                if not order.alive():
                    return
                order.cancel()

            elif msg.errorCode == 201:  # rejected
                if order.status == order.Rejected:
                    return
                order.reject()

            else:
                order.reject()  # default for all other cases

            self.notify(order)

    def push_orderstate(self, msg):
        with self._lock_orders:
            try:
                order = self.orderbyid[msg.orderId]
            except (KeyError, AttributeError):
                return  # no order or no id in error

            if msg.orderState.status in ['PendingCancel', 'Cancelled',
                                           'Canceled']:
                # This is most likely due to an expiration]
                order._willexpire = True
