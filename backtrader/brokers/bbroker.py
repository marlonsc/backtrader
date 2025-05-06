"""bbroker.py module.

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
import datetime

import backtrader as bt
from backtrader.order import BuyOrder, Order, SellOrder
from backtrader.position import Position
from backtrader.utils.py3 import integer_types, string_types

__all__ = ["BackBroker", "BrokerBack"]


class BackBroker(bt.BrokerBase):
    """Broker Simulator
The simulation supports different order types, checking a submitted order
cash requirements against current cash, keeping track of cash and value
for each iteration of ``cerebro`` and keeping the current position on
different datas.
*cash* is adjusted on each iteration for instruments like ``futures`` for
which a price change implies in real brokers the addition/substracion of
cash.
Supported order types:
- ``Market``: to be executed with the 1st tick of the next bar (namely
the ``open`` price)
- ``Close``: meant for intraday in which the order is executed with the
closing price of the last bar of the session
- ``Limit``: executes if the given limit price is seen during the
session
- ``Stop``: executes a ``Market`` order if the given stop price is seen
- ``StopLimit``: sets a ``Limit`` order in motion if the given stop
price is seen
Because the broker is instantiated by ``Cerebro`` and there should be
(mostly) no reason to replace the broker, the params are not controlled
by the user for the instance.  To change this there are two options:
1. Manually create an instance of this class with the desired params
and use ``cerebro.broker = instance`` to set the instance as the
broker for the ``run`` execution
2. Use the ``set_xxx`` to set the value using
``cerebro.broker.set_xxx`` where ```xxx`` stands for the name of the
parameter to set
.. note::
``cerebro.broker`` is a *property* supported by the ``getbroker``
and ``setbroker`` methods of ``Cerebro``"""

    params = (
        ("cash", 10000.0),
        ("checksubmit", True),
        ("eosbar", False),
        ("filler", None),
        # slippage options 滑点
        ("slip_perc", 0.0),
        ("slip_fixed", 0.0),
        ("slip_open", False),
        ("slip_match", True),
        ("slip_limit", True),
        ("slip_out", False),
        ("coc", False),
        ("coo", False),
        ("int2pnl", True),
        ("shortcash", True),
        ("fundstartval", 100.0),
        ("fundmode", False),
    )

    def __init__(self):
""""""
""""""
""""""
"""Set the actual fundmode (True or False)
If the argument fundstartval is not ``None``, it will used

Args::
    fundmode: 
    fundstartval: (Default value = None)"""
    fundstartval: (Default value = None)"""
        self.p.fundmode = fundmode
        if fundstartval is not None:
            self.set_fundstartval(fundstartval)

    def get_fundmode(self):
        """Returns the actual fundmode (True or False)"""
        return self.p.fundmode

    fundmode = property(get_fundmode, set_fundmode)

    def set_fundstartval(self, fundstartval):
"""Set the starting value of the fund-like performance tracker

Args::
    fundstartval:"""
    fundstartval:"""
        self.p.fundstartval = fundstartval

    def set_int2pnl(self, int2pnl):
"""Configure assignment of interest to profit and loss

Args::
    int2pnl:"""
    int2pnl:"""
        self.p.int2pnl = int2pnl

    def set_coc(self, coc):
"""Configure the Cheat-On-Close method to buy the close on order bar

Args::
    coc:"""
    coc:"""
        self.p.coc = coc

    def set_coo(self, coo):
"""Configure the Cheat-On-Open method to buy the close on order bar

Args::
    coo:"""
    coo:"""
        self.p.coo = coo

    def set_shortcash(self, shortcash):
"""Configure the shortcash parameters

Args::
    shortcash:"""
    shortcash:"""
        self.p.shortcash = shortcash

    def set_slippage_perc(
        self,
        perc,
        slip_open=True,
        slip_limit=True,
        slip_match=True,
        slip_out=False,
    ):
"""Configure slippage to be percentage based

Args::
    perc: 
    slip_open: (Default value = True)
    slip_limit: (Default value = True)
    slip_match: (Default value = True)
    slip_out: (Default value = False)"""
    slip_out: (Default value = False)"""
        self.p.slip_perc = perc
        self.p.slip_fixed = 0.0
        self.p.slip_open = slip_open
        self.p.slip_limit = slip_limit
        self.p.slip_match = slip_match
        self.p.slip_out = slip_out

    def set_slippage_fixed(
        self,
        fixed,
        slip_open=True,
        slip_limit=True,
        slip_match=True,
        slip_out=False,
    ):
"""Configure slippage to be fixed points based

Args::
    fixed: 
    slip_open: (Default value = True)
    slip_limit: (Default value = True)
    slip_match: (Default value = True)
    slip_out: (Default value = False)"""
    slip_out: (Default value = False)"""
        self.p.slip_perc = 0.0
        self.p.slip_fixed = fixed
        self.p.slip_open = slip_open
        self.p.slip_limit = slip_limit
        self.p.slip_match = slip_match
        self.p.slip_out = slip_out

    def set_filler(self, filler):
"""Sets a volume filler for volume filling execution

Args::
    filler:"""
    filler:"""
        self.p.filler = filler

    def set_checksubmit(self, checksubmit):
"""Sets the checksubmit parameter

Args::
    checksubmit:"""
    checksubmit:"""
        self.p.checksubmit = checksubmit

    def set_eosbar(self, eosbar):
"""Sets the eosbar parameter (alias: ``seteosbar``

Args::
    eosbar:"""
    eosbar:"""
        self.p.eosbar = eosbar

    seteosbar = set_eosbar

    def get_cash(self):
        """Returns the current cash (alias: ``getcash``)"""
        return self.cash

    getcash = get_cash

    def set_cash(self, cash):
"""Sets the cash parameter (alias: ``setcash``)

Args::
    cash:"""
    cash:"""
        self.startingcash = self.cash = self.p.cash = cash
        self._value = cash

    setcash = set_cash

    def add_cash(self, cash):
"""Add/Remove cash to the system (use a negative value to remove)

Args::
    cash:"""
    cash:"""
        self._cash_addition.append(cash)

    def get_fundshares(self):
        """Returns the current number of shares in the fund-like mode"""
        return self._fundshares

    fundshares = property(get_fundshares)

    def get_fundvalue(self):
        """Returns the Fund-like share value"""
        return self._fundval

    fundvalue = property(get_fundvalue)

    def cancel(self, order, bracket=False):
"""Args::
    order: 
    bracket: (Default value = False)"""
    bracket: (Default value = False)"""
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

    def get_value(self, datas=None, mkt=False, lever=False):
"""Returns the portfolio value of the given datas (if datas is ``None``, then
the total portfolio value will be returned (alias: ``getvalue``)

Args::
    datas: (Default value = None)
    mkt: (Default value = False)
    lever: (Default value = False)"""
    lever: (Default value = False)"""
        if datas is None:
            if mkt:
                return self._valuemkt if not lever else self._valuemktlever

            return self._value if not lever else self._valuelever

        return self._get_value(datas=datas, lever=lever)

    getvalue = get_value

    def get_value_lever(self, datas=None, mkt=False):
"""Args::
    datas: (Default value = None)
    mkt: (Default value = False)"""
    mkt: (Default value = False)"""
        return self.get_value(datas=datas, mkt=mkt)

    def _get_value(self, datas=None, lever=False):
"""Args::
    datas: (Default value = None)
    lever: (Default value = False)"""
    lever: (Default value = False)"""
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

            dunrealized = comminfo.profitandloss(
                position.size, position.price, data.close[0]
            )
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
                pos_value_unlever += dvalue / comminfo.get_leverage()
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
        # print(self.cash,pos_value_unlever,pos_value)
        self._valuemkt = pos_value_unlever

        self._valuelever = self.cash + pos_value
        self._valuemktlever = pos_value

        self._leverage = pos_value / (pos_value_unlever or 1.0)
        self._unrealized = unrealized

        return self._value if not lever else self._valuelever

    def get_leverage(self):
""""""
"""Returns an iterable with the orders which are still open (either not
executed or partially executed
The orders returned must not be touched.
If order manipulation is needed, set the parameter ``safe`` to True

Args::
    safe: (Default value = False)"""
    safe: (Default value = False)"""
        if safe:
            os = [x.clone() for x in self.pending]
        else:
            os = [x for x in self.pending]

        return os

    def getposition(self, data):
"""Returns the current position status (a ``Position`` instance) for
the given ``data``

Args::
    data:"""
    data:"""
        return self.positions[data]

    def orderstatus(self, order):
"""Args::
    order:"""
"""Args::
    order:"""
"""Args::
    order: 
    check: (Default value = True)"""
    check: (Default value = True)"""
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
"""Args::
    order: 
    check: (Default value = True)"""
    check: (Default value = True)"""
        if check and self.p.checksubmit:
            order.submit()
            self.submitted.append(order)
            self.orders.append(order)
            self.notify(order)
        else:
            self.submit_accept(order)

        return order

    def check_submitted(self):
""""""
"""Args::
    order:"""
"""Args::
    order: 
    cancel: (Default value = False)"""
    cancel: (Default value = False)"""
        oref = order.ref
        pref = getattr(order.parent, "ref", oref)
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
"""Args::
    order:"""
"""Args::
    order: 
    oco:"""
    oco:"""
        oref = order.ref
        if oco is None:
            self._ocos[oref] = oref  # current order is parent
            self._ocol[oref].append(oref)  # create ocogroup
        else:
            ocoref = self._ocos[oco.ref]  # ref to group leader
            self._ocos[oref] = ocoref  # ref to group leader
            self._ocol[ocoref].append(oref)  # add to group

    def add_order_history(self, orders, notify=True):
"""Args::
    orders: 
    notify: (Default value = True)"""
    notify: (Default value = True)"""
        oiter = iter(orders)
        o = next(oiter, None)
        self._userhist.append([o, oiter, notify])

    def set_fund_history(self, fund):
"""Args::
    fund:"""
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
    transmit: (Default value = True)
    histnotify: (Default value = False)
    _checksubmit: (Default value = True)"""
    _checksubmit: (Default value = True)"""

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
            histnotify=histnotify,
        )

        order.addinfo(**kwargs)
        self._ocoize(order, oco)

        return self.submit(order, check=_checksubmit)

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
        histnotify=False,
        _checksubmit=True,
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
    transmit: (Default value = True)
    histnotify: (Default value = False)
    _checksubmit: (Default value = True)"""
    _checksubmit: (Default value = True)"""

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
            histnotify=histnotify,
        )

        order.addinfo(**kwargs)
        self._ocoize(order, oco)

        return self.submit(order, check=_checksubmit)

    def _execute(
        self, order, ago=None, price=None, cash=None, position=None, dtcoc=None
    ):
"""Args::
    order: 
    ago: (Default value = None)
    price: (Default value = None)
    cash: (Default value = None)
    position: (Default value = None)
    dtcoc: (Default value = None)"""
    dtcoc: (Default value = None)"""
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
                cash += comminfo.cashadjust(-closed, position.adjbase, price)

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
                    cash += comminfo.cashadjust(adjsize, position.adjbase, price)

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
            order.execute(
                dtcoc or data.datetime[ago],
                execsize,
                price,
                closed,
                closedvalue,
                closedcomm,
                opened,
                openedvalue,
                openedcomm,
                comminfo.margin,
                pnl,
                psize,
                pprice,
            )

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
"""Args::
    order:"""
"""Args::
    order:"""
"""Args::
    order: 
    popen: 
    phigh: 
    plow:"""
    plow:"""
        if self.p.coc and order.info.get("coc", True):
            dtcoc = order.created.dt
            exprice = order.created.pclose
        else:
            if not self.p.coo and order.data.datetime[0] <= order.created.dt:
                return  # can only execute after creation time

            dtcoc = None
            exprice = popen

        if order.isbuy():
            p = self._slip_up(phigh, exprice, doslip=self.p.slip_open)
        else:
            p = self._slip_down(plow, exprice, doslip=self.p.slip_open)

        self._execute(order, ago=0, price=p, dtcoc=dtcoc)

    def _try_exec_close(self, order, pclose):
"""Args::
    order: 
    pclose:"""
    pclose:"""
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
"""Args::
    order: 
    popen: 
    phigh: 
    plow: 
    plimit:"""
    plimit:"""
        if order.isbuy():
            if plimit >= popen:
                # open smaller/equal than requested - buy cheaper
                pmax = min(phigh, plimit)
                p = self._slip_up(pmax, popen, doslip=self.p.slip_open, lim=True)
                self._execute(order, ago=0, price=p)
            elif plimit >= plow:
                # day low below req price ... match limit price
                self._execute(order, ago=0, price=plimit)

        else:  # Sell
            if plimit <= popen:
                # open greater/equal than requested - sell more expensive
                pmin = max(plow, plimit)
                p = self._slip_down(pmin, popen, doslip=self.p.slip_open, lim=True)
                self._execute(order, ago=0, price=p)
            elif plimit <= phigh:
                # day high above req price ... match limit price
                self._execute(order, ago=0, price=plimit)

    def _try_exec_stop(self, order, popen, phigh, plow, pcreated, pclose):
"""Args::
    order: 
    popen: 
    phigh: 
    plow: 
    pcreated: 
    pclose:"""
    pclose:"""
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

    def _try_exec_stoplimit(self, order, popen, phigh, plow, pclose, pcreated, plimit):
"""Args::
    order: 
    popen: 
    phigh: 
    plow: 
    pclose: 
    pcreated: 
    plimit:"""
    plimit:"""
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
"""Args::
    pmax: 
    price: 
    doslip: (Default value = True)
    lim: (Default value = False)"""
    lim: (Default value = False)"""
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
"""Args::
    pmin: 
    price: 
    doslip: (Default value = True)
    lim: (Default value = False)"""
    lim: (Default value = False)"""
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
"""Args::
    order:"""
""""""
""""""
""""""
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
                self.cash += comminfo.cashadjust(pos.size, pos.adjbase, data.close[0])
                # record the last adjustment price
                pos.adjbase = data.close[0]

        self._get_value()  # update value


# Alias
BrokerBack = BackBroker
