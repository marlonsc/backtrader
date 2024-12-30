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

import datetime
import backtrader as bt
import sys
import traceback
from backtrader.stores import ibstore_insync
from backtrader import Order
from backtrader.utils.py3 import with_metaclass

'''
LimitOrder = ibstore_insync.LimitOrder
MarketOrder = ibstore_insync.MarketOrder
StopOrder = ibstore_insync.StopOrder
StopLimitOrder = ibstore_insync.StopLimitOrder
OrderStatus = ibstore_insync.OrderStatus
OrderState = ibstore_insync.OrderState
OrderComboLeg = ibstore_insync.OrderComboLeg
Trade = ibstore_insync.Trade
BracketOrder = ibstore_insync.BracketOrder
OrderCondition = ibstore_insync.OrderCondition
PriceCondition = ibstore_insync.PriceCondition
TimeCondition = ibstore_insync.TimeCondition
MarginCondition = ibstore_insync.MarginCondition
ExecutionCondition = ibstore_insync.ExecutionCondition
VolumeCondition = ibstore_insync.VolumeCondition
PercentChangeCondition = ibstore_insync.PercentChangeCondition
'''

class MetaOrder(bt.MetaParams):
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
        ordertype = kwargs.get('orderType')
        kwargs['totalQuantity'] = kwargs.get('size', 0)
        kwargs['exectype'] = \
                cls._IBOrdTypes.get(ordertype, None)
        if ordertype in ['LMT']:
            kwargs['price'] = kwargs.get('lmtPrice', 0)
        elif ordertype in ['STP'] :
            kwargs['price'] = kwargs.get('auxPrice', 0)
        tif = kwargs.get('tif', None)
        if tif == 'DAY':
            kwargs['valid'] = datetime.timedelta(days=1)
        elif tif == 'GTC':
            kwargs['valid'] = datetime.timedelta(days=365)
        transmit = kwargs.get('transmit', None)
        
        _obj, args, kwargs =  \
            super().donew(*args, **kwargs)
        
        #在donew后处理同名参数
        if transmit is not None:
            kwargs['transmit'] = transmit
        # Return the object and arguments to the chain
        return _obj, args, kwargs

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


class IBOrder(with_metaclass(MetaOrder, Order, ibstore_insync.Order)):
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

    def __init__(self, **kwargs):

        #下面两个参数，在init前
        self._willexpire = False
        self.ordtype = self.Buy if kwargs.get('action') == 'BUY' else self.Sell
        self.ib = ibstore_insync.IBStoreInsync()
        self.broker = self.ib.broker

        super(IBOrder, self).__init__()
        ibstore_insync.Order.__init__(self, **kwargs)
        self.orderId=self.ib.nextOrderId()