"""oandabroker.py module.

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

from backtrader import (
    BrokerBase,
    BuyOrder,
    Order,
    SellOrder,
)
from backtrader.comminfo import CommInfoBase
from backtrader.position import Position
from backtrader.stores import oandastore
from backtrader.utils.py3 import with_metaclass


class OandaCommInfo(CommInfoBase):
""""""
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


class MetaOandaBroker(BrokerBase.__class__):
""""""
"""Class has already been created ... register

Args::
    name: 
    bases: 
    dct:"""
    dct:"""
        # Initialize the class
        super(MetaOandaBroker, cls).__init__(name, bases, dct)
        oandastore.OandaStore.BrokerCls = cls


class OandaBroker(with_metaclass(MetaOandaBroker, BrokerBase)):
    """Broker implementation for Oanda.
This class maps the orders/positions from Oanda to the
internal API of ``backtrader``."""

    params = (
        ("use_positions", True),
        ("commission", OandaCommInfo(mult=1.0, stocklike=False)),
    )

    def __init__(self, **kwargs):
        """"""
        super(OandaBroker, self).__init__()

        self.o = oandastore.OandaStore(**kwargs)

        self.orders = collections.OrderedDict()  # orders by order id
        self.notifs = collections.deque()  # holds orders which are notified

        self.opending = collections.defaultdict(list)  # pending transmission
        self.brackets = dict()  # confirmed brackets

        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0
        self.positions = collections.defaultdict(Position)

    def start(self):
""""""
"""Args::
    data:"""
""""""
""""""
"""Args::
    datas: (Default value = None)"""
"""Args::
    data: 
    clone: (Default value = True)"""
    clone: (Default value = True)"""
        # return self.o.getposition(data._dataname, clone=clone)
        pos = self.positions[data._dataname]
        if clone:
            pos = pos.clone()

        return pos

    def orderstatus(self, order):
"""Args::
    order:"""
"""Args::
    oref:"""
"""Args::
    oref:"""
"""Args::
    oref:"""
"""Args::
    oref:"""
"""Args::
    oref:"""
"""Args::
    order:"""
"""Args::
    order: 
    cancel: (Default value = False)"""
    cancel: (Default value = False)"""
        pref = getattr(order.parent, "ref", order.ref)  # parent ref or self
        br = self.brackets.pop(pref, None)  # to avoid recursion
        if br is None:
            return

        if not cancel:
            if len(br) == 3:  # all 3 orders in place, parent was filled
                br = br[1:]  # discard index 0, parent
                for o in br:
                    o.activate()  # simulate activate for children
                self.brackets[pref] = br  # not done - reinsert children

            elif len(br) == 2:  # filling a children
                oidx = br.index(order)  # find index to filled (0 or 1)
                self._cancel(br[1 - oidx].ref)  # cancel remaining (1 - 0 -> 1)
        else:
            # Any cancellation cancel the others
            for o in br:
                if o.alive():
                    self._cancel(o.ref)

    def _fill(self, oref, size, price, ttype, **kwargs):
"""Args::
    oref: 
    size: 
    price: 
    ttype:"""
    ttype:"""
        order = self.orders[oref]

        if not order.alive():  # can be a bracket
            pref = getattr(order.parent, "ref", order.ref)
            if pref not in self.brackets:
                msg = (
                    "Order fill received for {}, with price {} and size {} "
                    "but order is no longer alive and is not a bracket. "
                    "Unknown situation"
                )
                msg.format(order.ref, price, size)
                self.put_notification(msg, order, price, size)
                return

            # [main, stopside, takeside], neg idx to array are -3, -2, -1
            if ttype == "STOP_LOSS_FILLED":
                order = self.brackets[pref][-2]
            elif ttype == "TAKE_PROFIT_FILLED":
                order = self.brackets[pref][-1]
            else:
                msg = (
                    "Order fill received for {}, with price {} and size {} "
                    "but order is no longer alive and is a bracket. "
                    "Unknown situation"
                )
                msg.format(order.ref, price, size)
                self.put_notification(msg, order, price, size)
                return

        data = order.data
        pos = self.getposition(data, clone=False)
        psize, pprice, opened, closed = pos.update(size, price)

        self.getcommissioninfo(data)

        closedvalue = closedcomm = 0.0
        openedvalue = openedcomm = 0.0
        margin = pnl = 0.0

        order.execute(
            data.datetime[0],
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
        )

        if order.executed.remsize:
            order.partial()
            self.notify(order)
        else:
            order.completed()
            self.notify(order)
            self._bracketize(order)

    def _transmit(self, order):
"""Args::
    order:"""
"""Args::
    owner: 
    data: 
    size: 
    price: (Default value = None)
    plimit: (Default value = None)
    exectype: (Default value = None)
    valid: (Default value = None)
    tradeid: (Default value = 0)
    oco: (Default value = None)
    trailamount: (Default value = None)
    trailpercent: (Default value = None)
    parent: (Default value = None)
    transmit: (Default value = True)"""
    transmit: (Default value = True)"""

        order = BuyOrder(
            owner=owner,
            data=data,
            size=size,
            price=price,
            pricelimit=plimit,
            exectype=exectype,
            valid=valid,
            tradeid=tradeid,
            trailamount=trailamount,
            trailpercent=trailpercent,
            parent=parent,
            transmit=transmit,
        )

        order.addinfo(**kwargs)
        order.addcomminfo(self.getcommissioninfo(data))
        return self._transmit(order)

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
        oco=None,
        trailamount=None,
        trailpercent=None,
        parent=None,
        transmit=True,
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
    tradeid: (Default value = 0)
    oco: (Default value = None)
    trailamount: (Default value = None)
    trailpercent: (Default value = None)
    parent: (Default value = None)
    transmit: (Default value = True)"""
    transmit: (Default value = True)"""

        order = SellOrder(
            owner=owner,
            data=data,
            size=size,
            price=price,
            pricelimit=plimit,
            exectype=exectype,
            valid=valid,
            tradeid=tradeid,
            trailamount=trailamount,
            trailpercent=trailpercent,
            parent=parent,
            transmit=transmit,
        )

        order.addinfo(**kwargs)
        order.addcomminfo(self.getcommissioninfo(data))
        return self._transmit(order)

    def cancel(self, order):
"""Args::
    order:"""
"""Args::
    order:"""
""""""
""""""
        self.notifs.append(None)  # mark notification boundary
