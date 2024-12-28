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

__all__ = ['IBOrder', 'IBBroker']

import collections
from copy import copy
from datetime import date, datetime, timedelta
import threading
import uuid

from backtrader.feed import DataBase
from backtrader import (TimeFrame, num2date, date2num, BrokerBase,
                        Order, OrderBase, OrderData)
from backtrader.utils.py3 import bytes, bstr, with_metaclass, queue, MAXFLOAT
from backtrader.metabase import MetaParams
from backtrader.commissions.ibcommission import IBCommInfo
from backtrader.position import Position
from backtrader.stores import ibstore_insync
from backtrader.utils import AutoDict, AutoOrderedDict


'''
bytes = bstr  # py2/3 need for ibpy

class IBOrderState(object):
    # wraps OrderState object and can print it
    _fields = ['status', 'initMargin', 'maintMargin', 'equityWithLoan',
               'commission', 'minCommission', 'maxCommission',
               'commissionCurrency', 'warningText']

    def __init__(self, orderstate):
        for f in self._fields:
             # fname = 'm_' + f
            fname =  f
            setattr(self, fname, getattr(orderstate, fname))

    def __str__(self):
        txt = list()
        txt.append('--- ORDERSTATE BEGIN')
        for f in self._fields:
            # fname = 'm_' + f
            fname = f
            txt.append('{}: {}'.format(f.capitalize(), getattr(self, fname)))
        txt.append('--- ORDERSTATE END')
        return '\n'.join(txt)
'''

class IBOrder(OrderBase,  ibstore_insync.Order):
    '''
    Subclasses the IBPy order to provide the minimum extra functionality
    needed to be compatible with the internally defined orders

    Once ``OrderBase`` has processed the parameters, the __init__ method takes
    over to use the parameter values and set the appropriate values in the
    ib.ext.Order.Order object

    Any extra parameters supplied with kwargs are applied directly to the
    ib.ext.Order.Order object, which could be used as follows::

    Example: if the 4 order execution types directly supported by
      ``backtrader`` are not enough, in the case of for example
      *Interactive Brokers* the following could be passed as *kwargs*::

        orderType='LIT', lmtPrice=10.0, auxPrice=9.8

      This would override the settings created by ``backtrader`` and
      generate a ``LIMIT IF TOUCHED`` order with a *touched* price of 9.8
      and a *limit* price of 10.0.

    This would be done almost always from the ``Buy`` and ``Sell`` methods of
    the ``Strategy`` subclass being used in ``Cerebro``
    '''

    def __str__(self):
        '''
        #Get the printout from the base class and add some ib.Order specific
        #fields
        '''
        basetxt = ibstore_insync.Order.__str__()
        tojoin = [basetxt]
        tojoin.append('Ref: {}'.format(self.ref))
        tojoin.append('orderId: {}'.format(self.orderId))
        tojoin.append('Action: {}'.format(self.action))
        tojoin.append('Size (ib): {}'.format(self.totalQuantity))
        tojoin.append('Lmt Price: {}'.format(self.lmtPrice))
        tojoin.append('Aux Price: {}'.format(self.auxPrice))
        tojoin.append('orderType: {}'.format(self.orderType))
        tojoin.append('Tif (Time in Force): {}'.format(self.tif))
        tojoin.append('GoodTillDate: {}'.format(self.goodTillDate))
        return '\n'.join(tojoin)

    # Map backtrader order types to the ib specifics
    _IBOrdTypes = {
        None: None,  # default
        'MKT' : Order.Market,
        'LMT' : Order.Limit,
        'MOC' : Order.Close,
        'STP' : Order.Stop,
        'STPLMT' : Order.StopLimit,
        'TRAIL' : Order.StopTrail,
        'TRAIL LIMIT' : Order.StopTrailLimit,
    }
        
    def donew(cls, *args, **kwargs):
        '''
        本函数完成从ib_incync的初始化参数到backtrader的order类的参数的转换
        ibbroker使用的是ib_insync的order类，需要兼容backtrader的order类,因此将
        ib_incync的初始化参数转化为backtrader的order类的参数,以完成后面的类初始化
        本函数需要在对象生成前调用，不能放在对象的__init__函数中
        ('owner', None), 
        ('data', None),
        ('size', None), 
        ('price', None), 
        ('pricelimit', None),
        ('exectype', None), 
        ('valid', None), 
        ('tradeid', 0), 
        ('oco', None),
        ('trailamount', None), 
        ('trailpercent', None),
        ('parent', None), 
        ('transmit', True),
        ('simulated', False),
        # To support historical order evaluation
        ('histnotify', False),
        ('orderId', 0),
        '''
        kwargs['totalQuantity'] = kwargs.get('size', 0)
        kwargs['exectype'] = \
                cls._IBOrdTypes.get(kwargs.get('orderType'), None)
        kwargs['pricelimit'] = kwargs.get('lmtPrice', 0)
        tif = kwargs.get('tif', None)
        if tif == 'DAY':
            kwargs['valid'] = datetime.timedelta(days=1)
        elif tif == 'GTC':
            kwargs['valid'] = datetime.timedelta(days=365)

        _obj, args, kwargs =  \
            super().donew(*args, **kwargs)
        # Return the object and arguments to the chain
        return _obj, args, kwargs

    def __init__(self, action=None, totalQuantity=0, orderType=None,**kwargs):

        #下面两个参数，在init前
        self._willexpire = False
        self.ordtype = self.Buy if action.upper() == 'BUY' else self.Sell
        self.ib = ibstore_insync.IBStoreInsync()
        self.broker = self.ib.broker
        # Marker to indicate an openOrder has been seen with
        # PendinCancel/Cancelled which is indication of an upcoming
        # cancellation
        assert action.upper() in ('BUY', 'SELL')
        reverseAction = 'BUY' if action.upper() == 'SELL' else 'SELL'

        super(IBOrder, self).__init__()
        ibstore_insync.Order.__init__(self, **kwargs)
        self.orderId=self.ib.nextOrderId(),

class MetaIBBroker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaIBBroker, cls).__init__(name, bases, dct)
        #ibstore.IBStore.BrokerCls = cls
        ibstore_insync.IBStoreInsync.BrokerCls = cls
        


class IBBroker(with_metaclass(MetaIBBroker, BrokerBase)):
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
    )

    def __init__(self, **kwargs):
        super(IBBroker, self).__init__()

        self.ib.start(broker=self)

        if self.ib.isConnected():
            self.startingcash = self.cash = self.ib.get_acc_cash()
            self.startingvalue = self.value = self.ib.get_acc_value()

        self.submitted = collections.deque()
        print(f"cash: {self.startingcash}")

    def init(self):
        '''
        init会在super().__init__中调用,
        因此init的执行是在__init__中的第一句被调用,__init__中初始化的代码都init()后执行
        '''

        super(IBBroker, self).init()

        self.ib = ibstore_insync.IBStoreInsync()
        self.runmode = self.ib.runmode

        self.startingcash = self.cash = self.p.cash
        self.startingvalue = self.value = 0.0

        self.orders = list()  # will only be appending
        self.pending = collections.deque()  # popleft and append(right)
        self._toactivate = collections.deque()  # to activate in next cycle

        self.positions = collections.defaultdict(Position)
        self._lock_orders = threading.Lock()  # control access
        self.orderbyid = dict()  # orders by order id
        self.executions = dict()  # notified executions
        self.ordstatus = collections.defaultdict(dict)
        self.d_credit = collections.defaultdict(float)  # credit per data
        self.notifs = queue.Queue()
        self.tonotify = collections.deque()  # hold oids to be notified

        self.submitted = collections.deque()

        # to keep dependent orders if needed
        self._pchildren = collections.defaultdict(collections.deque)

        self._ocos = dict()
        self._ocol = collections.defaultdict(list) 
       
    def get_cash(self):
        # This call cannot block if no answer is available from ib
        self.cash = self.ib.get_acc_cash()
        return self.cash
    getcash = get_cash

    def get_value(self, datas=None):
        self.value = self.ib.get_acc_value()
        return self.value
    getvalue = get_value

    def getposition(self, data, clone=True):
        return self.ib.getposition(data=data, clone=clone)

    def cancel(self, order):
        try:
            o = self.orderbyid[order.orderId]
        except (ValueError, KeyError):
            return  # not found ... not cancellable

        if order.status == Order.Cancelled:  # already cancelled
            return

        self.ib.cancelOrder(order.orderId)

    def orderstatus(self, order):
        try:
            o = self.orderbyid[order.orderId]
        except (ValueError, KeyError):
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
    
    def submit(self, order):
        
        order.submit(self)

        # ocoize if needed
        if order.oco is None:  # Generate a UniqueId
            order.OcaGroup = uuid.uuid4().bytes
        else:
            order.OcaGroup = self.orderbyid[order.oco.orderId].OcaGroup

        self.orderbyid[order.orderId] = order 
        self.ib.placeOrder(order.data.tradecontract, order)
        self.notify(order)

        return order

    def transmit(self, order, check=True):
        if self.runmode == 'backtest':
            if check and self.p.checksubmit:
                order.submit()
                self.submitted.append(order)
                self.orders.append(order)
                self.notify(order)
            else:
                self.submit_accept(order)

        return order

    def check_submitted(self):
        if self.runmode == 'backtest':
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

    def getcommissioninfo(self, data):
        if data.commission is None:
            contract = data.tradecontract
            try:
                mult = float(contract.multiplier)
            except (ValueError, TypeError):
                mult = 1.0
            stocklike = contract.secType not in ('FUT', 'OPT', 'FOP',)
            return IBCommInfo(mult=mult, stocklike=stocklike)
        else:
            return data.commission

    def _makeorder(self, action, owner, data, **kwargs):
        '''
        开仓必须使用BKT bracketOrder 套利单
        平仓必须使用LMT limitOrder 限价单
        '''
        orderId=self.ib.nextOrderId()
        order = IBOrder(action=action, 
                        owner=owner, 
                        data=data, 
                        orderId=orderId,
                        **kwargs)

        order.addcomminfo(self.getcommissioninfo(data))
        return order
            
    def buy(self, owner, data, **kwargs):
        order = self._makeorder('BUY', owner, data, **kwargs)
        order.addinfo(**kwargs)
        self._ocoize(order, oco)
        return self.submit(order)

    def sell(self, owner, data, **kwargs):
        order = self._makeorder('SELL', owner, data, **kwargs)
        order.addinfo(**kwargs)
        self._ocoize(order, oco)
        return self.submit(order)
    

    def notify(self, order):
        self.notifs.put(order.clone())

    def get_notification(self):
        try:
            return self.notifs.get(False)
        except queue.Empty:
            pass

        return None

    def next(self):
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

            elif not order.active():
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
