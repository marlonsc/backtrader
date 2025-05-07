"""vcbroker.py module.

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
import threading
from datetime import date, datetime, timedelta

from backtrader import BrokerBase, BuyOrder, Order, SellOrder
from backtrader.comminfo import CommInfoBase
from backtrader.position import Position
from backtrader.stores import vcstore
from backtrader.utils.py3 import with_metaclass


class VCCommInfo(CommInfoBase):
    """Commissions are calculated by ib, but the trades calculations in the
```Strategy`` rely on the order carrying a CommInfo object attached for the
calculation of the operation cost and value.
These are non-critical informations, but removing them from the trade could
break existing usage and it is better to provide a CommInfo objet which
enables those calculations even if with approvimate values.
The margin calculation is not a known in advance information with IB
(margin impact can be gotten from OrderState objects) and therefore it is
left as future exercise to get it"""

    def getvaluesize(self, size, price):
"""Args::
    size: 
    price:"""
    price:"""
        # In real life the margin approaches the price
        return abs(size) * price

    def getoperationcost(self, size, price):
"""Returns the needed amount of cash an operation would cost

Args::
    size: 
    price:"""
    price:"""
        # Same reasoning as above
        return abs(size) * price


class MetaVCBroker(BrokerBase.__class__):
""""""
"""Class has already been created ... register

Args::
    name: 
    bases: 
    dct:"""
    dct:"""
        # Initialize the class
        super(MetaVCBroker, cls).__init__(name, bases, dct)
        vcstore.VCStore.BrokerCls = cls


class VCBroker(with_metaclass(MetaVCBroker, BrokerBase)):
    """Broker implementation for VisualChart.
This class maps the orders/positions from VisualChart to the
internal API of ``backtrader``."""

    params = (
        ("account", None),
        ("commission", None),
    )

    def __init__(self, **kwargs):
        """"""
        super(VCBroker, self).__init__()

        self.store = vcstore.VCStore(**kwargs)

        # Account data
        self._acc_name = None
        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0

        # Position accounting
        self._lock_pos = threading.Lock()  # sync account updates
        self.positions = collections.defaultdict(Position)  # actual positions

        # Order storage
        self._lock_orders = threading.Lock()  # control access
        self.orderbyid = dict()  # orders by order id

        # Notifications
        self.notifs = collections.deque()

        # Dictionaries of values for order mapping
        self._otypes = {
            Order.Market: self.store.vcctmod.OT_Market,
            Order.Close: self.store.vcctmod.OT_Market,
            Order.Limit: self.store.vcctmod.OT_Limit,
            Order.Stop: self.store.vcctmod.OT_StopMarket,
            Order.StopLimit: self.store.vcctmod.OT_StopLimit,
        }

        self._osides = {
            Order.Buy: self.store.vcctmod.OS_Buy,
            Order.Sell: self.store.vcctmod.OS_Sell,
        }

        self._otrestriction = {
            Order.T_None: self.store.vcctmod.TR_NoRestriction,
            Order.T_Date: self.store.vcctmod.TR_Date,
            Order.T_Close: self.store.vcctmod.TR_CloseAuction,
            Order.T_Day: self.store.vcctmod.TR_Session,
        }

        self._ovrestriction = {
            Order.V_None: self.store.vcctmod.VR_NoRestriction,
        }

        self._futlikes = (
            self.store.vcdsmod.IT_Future,
            self.store.vcdsmod.IT_Option,
            self.store.vcdsmod.IT_Fund,
        )

    def start(self):
""""""
""""""
""""""
"""Args::
    datas: (Default value = None)"""
""""""
"""Args::
    order:"""
""""""
"""Args::
    data: 
    clone: (Default value = True)"""
    clone: (Default value = True)"""
        with self._lock_pos:
            pos = self.positions[data._tradename]
            if clone:
                return pos.clone()

        return pos

    def getcommissioninfo(self, data):
"""Args::
    data:"""
"""Args::
    ordtype: 
    owner: 
    data: 
    size: 
    price: (Default value = None)
    plimit: (Default value = None)
    exectype: (Default value = None)
    valid: (Default value = None)
    tradeid: (Default value = 0)"""
    tradeid: (Default value = 0)"""

        order = self.store.vcctmod.Order()
        order.Account = self._acc_name
        order.SymbolCode = data._tradename
        order.OrderType = self._otypes[exectype]
        order.OrderSide = self._osides[ordtype]

        order.VolumeRestriction = self._ovrestriction[Order.V_None]
        order.HideVolume = 0
        order.MinVolume = 0

        # order.UserName = 'danjrod'  # str(tradeid)
        # order.OrderId = 'a' * 50  # str(tradeid)
        order.UserOrderId = ""
        if tradeid:
            order.ExtendedInfo = "TradeId {}".format(tradeid)
        else:
            order.ExtendedInfo = ""

        order.Volume = abs(size)

        order.StopPrice = 0.0
        order.Price = 0.0
        if exectype == Order.Market:
            pass
        elif exectype == Order.Limit:
            order.Price = price or plimit  # cover naming confusion cases
        elif exectype == Order.Close:
            pass
        elif exectype == Order.Stop:
            order.StopPrice = price
        elif exectype == Order.StopLimit:
            order.StopPrice = price
            order.Price = plimit

        order.ValidDate = None
        if exectype == Order.Close:
            order.TimeRestriction = self._otrestriction[Order.T_Close]
        else:
            if valid is None:
                order.TimeRestriction = self._otrestriction[Order.T_None]
            elif isinstance(valid, (datetime, date)):
                order.TimeRestriction = self._otrestriction[Order.T_Date]
                order.ValidDate = valid
            elif isinstance(valid, (timedelta,)):
                if valid == Order.DAY:
                    order.TimeRestriction = self._otrestriction[Order.T_Day]
                else:
                    order.TimeRestriction = self._otrestriction[Order.T_Date]
                    order.ValidDate = datetime.now() + valid

            elif not self.valid:  # DAY
                order.TimeRestriction = self._otrestriction[Order.T_Day]

        # Support for custom user arguments
        for k in kwargs:
            if hasattr(order, k):
                setattr(order, k, kwargs[k])

        return order

    def submit(self, order, vcorder):
"""Args::
    order: 
    vcorder:"""
    vcorder:"""
        order.submit(self)

        vco = vcorder
        oid = self.store.vcct.SendOrder(
            vco.Account,
            vco.SymbolCode,
            vco.OrderType,
            vco.OrderSide,
            vco.Volume,
            vco.Price,
            vco.StopPrice,
            vco.VolumeRestriction,
            vco.TimeRestriction,
            ValidDate=vco.ValidDate,
        )

        order.vcorder = oid
        order.addcomminfo(self.getcommissioninfo(order.data))

        with self._lock_orders:
            self.orderbyid[oid] = order
        self.notify(order)
        return order

    def buy(
        self,
        owner,
        data,
        size,
        price=None,
        plimit=None,
        exectype=None,
        valid=None,
        tradeid=0,
        **kwargs,
    ):
"""Args::
    owner: 
    data: 
    size: 
    price: (Default value = None)
    plimit: (Default value = None)
    exectype: (Default value = None)
    valid: (Default value = None)
    tradeid: (Default value = 0)"""
    tradeid: (Default value = 0)"""

        order = BuyOrder(
            owner=owner,
            data=data,
            size=size,
            price=price,
            pricelimit=plimit,
            exectype=exectype,
            valid=valid,
            tradeid=tradeid,
        )

        order.addinfo(**kwargs)

        vcorder = self._makeorder(
            order.ordtype,
            owner,
            data,
            size,
            price,
            plimit,
            exectype,
            valid,
            tradeid,
            **kwargs,
        )

        return self.submit(order, vcorder)

    def sell(
        self,
        owner,
        data,
        size,
        price=None,
        plimit=None,
        exectype=None,
        valid=None,
        tradeid=0,
        **kwargs,
    ):
"""Args::
    owner: 
    data: 
    size: 
    price: (Default value = None)
    plimit: (Default value = None)
    exectype: (Default value = None)
    valid: (Default value = None)
    tradeid: (Default value = 0)"""
    tradeid: (Default value = 0)"""

        order = SellOrder(
            owner=owner,
            data=data,
            size=size,
            price=price,
            pricelimit=plimit,
            exectype=exectype,
            valid=valid,
            tradeid=tradeid,
        )

        order.addinfo(**kwargs)

        vcorder = self._makeorder(
            order.ordtype,
            owner,
            data,
            size,
            price,
            plimit,
            exectype,
            valid,
            tradeid,
            **kwargs,
        )

        return self.submit(order, vcorder)

    #
    # COM Events implementation
    #
    def __call__(self, trader):
"""Args::
    trader:"""
"""Args::
    Account:"""
"""Args::
    Order:"""
"""Args::
    Order:"""
"""Args::
    Order:"""
"""Args::
    Order:"""
"""Args::
    Order: 
    partial:"""
    partial:"""
        with self._lock_orders:
            try:
                border = self.orderbyid[Order.OrderId]
            except KeyError:
                return  # possibly external order

        price = Order.Price
        size = Order.Volume
        if border.issell():
            size *= -1

        # Find position and do a real update - accounting happens here
        position = self.getposition(border.data, clone=False)
        pprice_orig = position.price
        psize, pprice, opened, closed = position.update(size, price)

        comminfo = border.comminfo
        closedvalue = comminfo.getoperationcost(closed, pprice_orig)
        closedcomm = comminfo.getcommission(closed, price)

        openedvalue = comminfo.getoperationcost(opened, price)
        openedcomm = comminfo.getcommission(opened, price)

        pnl = comminfo.profitandloss(-closed, pprice_orig, price)
        margin = comminfo.getvaluesize(size, price)

        # NOTE: No commission information available in the Trader interface
        # CHECK: Use reported time instead of last data time?
        border.execute(
            border.data.datetime[0],
            size,
            price,
            closed,
            closedvalue,
            closedcomm,
            opened,
            openedvalue,
            openedcomm,
            margin,
            pnl,
            psize,
            pprice,
        )  # pnl

        if partial:
            border.partial()
        else:
            border.completed()

        self.notify(border)

    def OnOrderInMarket(self, Order):
"""Args::
    Order:"""
"""Args::
    Order:"""
"""Args::
    Account:"""
"""Args::
    Account:"""
""""""
"""Args::
    p1: 
    p2: 
    p3:"""
    p3:"""
