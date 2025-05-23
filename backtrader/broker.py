#!/usr/bin/env python
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

from .comminfo import CommInfoBase
from .metabase import MetaParams
from .utils.py3 import with_metaclass


class MetaBroker(MetaParams):
    """ """

    def __new__(cls, name, bases, dct):
        """Class has already been created ... fill missing methods if needed be

        :param name:
        :param bases:
        :param dct:

        """
        # Initialize the class
        new_cls = super(MetaBroker, cls).__new__(cls, name, bases, dct)
        translations = {
            "get_cash": "getcash",
            "get_value": "getvalue",
        }

        for attr, trans in translations.items():
            if not hasattr(new_cls, attr):
                setattr(new_cls, attr, getattr(new_cls, trans))
        return new_cls


class BrokerBase(with_metaclass(MetaBroker, object)):
    """ """

    params = (("commission", CommInfoBase()),)

    def __init__(self):
        """ """
        if not hasattr(self, "p"):
            self.p = type("Params", (), dict(self.params))()
        self.comminfo = dict()
        self.init()

    def init(self):
        """ """
        # called from init and from start
        if None not in self.comminfo:
            self.comminfo = dict({None: self.p.commission})

    def start(self):
        """ """
        self.init()

    def stop(self):
        """ """

    def add_order_history(self, orders, notify=False):
        """Add order history. See cerebro for details

        :param orders:
        :param notify:  (Default value = False)

        """
        raise NotImplementedError

    def set_fund_history(self, fund):
        """Add fund history. See cerebro for details

        :param fund:

        """
        raise NotImplementedError

    def getcommissioninfo(self, data):
        """Retrieves the ``CommissionInfo`` scheme associated with the given
        ``data``

        :param data:

        """
        if data._name in self.comminfo:
            return self.comminfo[data._name]

        return self.comminfo[None]

    def setcommission(
        self,
        commission=0.0,
        margin=None,
        mult=1.0,
        commtype=None,
        percabs=True,
        stocklike=False,
        interest=0.0,
        interest_long=False,
        leverage=1.0,
        automargin=False,
        name=None,
    ):
        """This method sets a `` CommissionInfo`` object for assets managed in
        the broker with the parameters. Consult the reference for
        ``CommInfoBase``

        If name is ``None``, this will be the default for assets for which no
        other ``CommissionInfo`` scheme can be found

        :param commission:  (Default value = 0.0)
        :param margin:  (Default value = None)
        :param mult:  (Default value = 1.0)
        :param commtype:  (Default value = None)
        :param percabs:  (Default value = True)
        :param stocklike:  (Default value = False)
        :param interest:  (Default value = 0.0)
        :param interest_long:  (Default value = False)
        :param leverage:  (Default value = 1.0)
        :param automargin:  (Default value = False)
        :param name:  (Default value = None)

        """

        comm = CommInfoBase()
        comm.commission = commission
        comm.margin = margin
        comm.mult = mult
        comm.commtype = commtype
        comm.stocklike = stocklike
        comm.percabs = percabs
        comm.interest = interest
        comm.interest_long = interest_long
        comm.leverage = leverage
        comm.automargin = automargin
        self.comminfo[name] = comm

    def addcommissioninfo(self, comminfo, name=None):
        """Adds a ``CommissionInfo`` object that will be the default for all assets if
        ``name`` is ``None``

        :param comminfo:
        :param name:  (Default value = None)

        """
        self.comminfo[name] = comminfo

    def getcash(self):
        """ """
        raise NotImplementedError

    def getvalue(self, datas=None):
        """

        :param datas:  (Default value = None)

        """
        raise NotImplementedError

    def get_fundshares(self):
        """Returns the current number of shares in the fund-like mode"""
        return 1.0  # the abstract mode has only 1 share

    fundshares = property(get_fundshares)

    def get_fundvalue(self):
        """ """
        return self.getvalue()

    fundvalue = property(get_fundvalue)

    def set_fundmode(self, fundmode, fundstartval=None):
        """Set the actual fundmode (True or False)

        If the argument fundstartval is not ``None``, it will used

        :param fundmode:
        :param fundstartval:  (Default value = None)

        """
        pass  # do nothing, not all brokers can support this

    def get_fundmode(self):
        """Returns the actual fundmode (True or False)"""
        return False

    fundmode = property(get_fundmode, set_fundmode)

    def getposition(self, data):
        """

        :param data:

        """
        raise NotImplementedError

    def submit(self, order):
        """

        :param order:

        """
        raise NotImplementedError

    def cancel(self, order):
        """

        :param order:

        """
        raise NotImplementedError

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
        oco=None,
        trailamount=None,
        trailpercent=None,
        **kwargs,
    ):
        """

        :param owner:
        :param data:
        :param size:
        :param price:  (Default value = None)
        :param plimit:  (Default value = None)
        :param exectype:  (Default value = None)
        :param valid:  (Default value = None)
        :param tradeid:  (Default value = 0)
        :param oco:  (Default value = None)
        :param trailamount:  (Default value = None)
        :param trailpercent:  (Default value = None)
        :param **kwargs:

        """

        raise NotImplementedError

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
        **kwargs,
    ):
        """

        :param owner:
        :param data:
        :param size:
        :param price:  (Default value = None)
        :param plimit:  (Default value = None)
        :param exectype:  (Default value = None)
        :param valid:  (Default value = None)
        :param tradeid:  (Default value = 0)
        :param oco:  (Default value = None)
        :param trailamount:  (Default value = None)
        :param trailpercent:  (Default value = None)
        :param **kwargs:

        """

        raise NotImplementedError

    def next(self):
        """ """


# __all__ = ['BrokerBase', 'fillers', 'filler']
