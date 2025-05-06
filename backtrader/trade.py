"""trade.py module.

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

import itertools

try:
    from .utils import AutoOrderedDict
except ImportError:

"""AutoOrderedDict class.

Description of the class functionality."""
        pass


from .utils.date import num2date
from .utils.py3 import range


class TradeHistory(AutoOrderedDict):
    """Represents the status and update event for each update a Trade has
This object is a dictionary which allows '.' notation"""

    def __init__(
        self,
        status,
        dt,
        barlen,
        size,
        price,
        value,
        pnl,
        pnlcomm,
        tz,
        event=None,
    ):
"""Initializes the object to the current status of the Trade

Args::
    status: 
    dt: 
    barlen: 
    size: 
    price: 
    value: 
    pnl: 
    pnlcomm: 
    tz: 
    event: (Default value = None)"""
    event: (Default value = None)"""
        super(TradeHistory, self).__init__()
        self.status.status = status
        self.status.dt = dt
        self.status.barlen = barlen
        self.status.size = size
        self.status.price = price
        self.status.value = value
        self.status.pnl = pnl
        self.status.pnlcomm = pnlcomm
        self.status.tz = tz
        if event is not None:
            self.event = event

    def __reduce__(self):
""""""
"""Used to fill the ``update`` part of the history entry

Args::
    order: 
    size: 
    price: 
    commission:"""
    commission:"""
        self.event.order = order
        self.event.size = size
        self.event.price = price
        self.event.commission = commission

        # Do not allow updates (avoids typing errors)
        self._close()

    def datetime(self, tz=None, naive=True):
"""Returns a datetime for the time the update event happened

Args::
    tz: (Default value = None)
    naive: (Default value = True)"""
    naive: (Default value = True)"""
        return num2date(self.status.dt, tz or self.status.tz, naive)


class Trade(object):
    """Keeps track of the life of an trade: size, price,
commission (and value?)
An trade starts at 0 can be increased and reduced and can
be considered closed if it goes back to 0.
The trade can be long (positive size) or short (negative size)
An trade is not meant to be reversed (no support in the logic for it)
Member Attributes:
- ``ref``: unique trade identifier
- ``status`` (``int``): one of Created, Open, Closed
- ``tradeid``: grouping tradeid passed to orders during creation
The default in orders is 0
- ``size`` (``int``): current size of the trade
- ``price`` (``float``): current price of the trade
- ``value`` (``float``): current value of the trade
- ``commission`` (``float``): current accumulated commission
- ``pnl`` (``float``): current profit and loss of the trade (gross pnl)
- ``pnlcomm`` (``float``): current profit and loss of the trade minus
commission (net pnl)
- ``isclosed`` (``bool``): records if the last update closed (set size to
null the trade
- ``isopen`` (``bool``): records if any update has opened the trade
- ``justopened`` (``bool``): if the trade was just opened
- ``baropen`` (``int``): bar in which this trade was opened
- ``dtopen`` (``float``): float coded datetime in which the trade was
opened
- Use method ``open_datetime`` to get a Python datetime.datetime
or use the platform provided ``num2date`` method
- ``barclose`` (``int``): bar in which this trade was closed
- ``dtclose`` (``float``): float coded datetime in which the trade was
closed
- Use method ``close_datetime`` to get a Python datetime.datetime
or use the platform provided ``num2date`` method
- ``barlen`` (``int``): number of bars this trade was open
- ``historyon`` (``bool``): whether history has to be recorded
- ``history`` (``list``): holds a list updated with each "update" event
containing the resulting status and parameters used in the update
The first entry in the history is the Opening Event
The last entry in the history is the Closing Event"""

    refbasis = itertools.count(1)

    status_names = ["Created", "Open", "Closed"]
    Created, Open, Closed = range(3)

    def __str__(self):
""""""
"""Args::
    data: (Default value = None)
    tradeid: (Default value = 0)
    historyon: (Default value = False)
    size: (Default value = 0)
    price: (Default value = 0.0)
    value: (Default value = 0.0)
    commission: (Default value = 0.0)"""
    commission: (Default value = 0.0)"""

        self.ref = next(self.refbasis)
        self.data = data
        self.tradeid = tradeid
        self.size = size
        self.price = price
        self.value = value
        self.commission = commission

        self.pnl = 0.0
        self._pnlentrysum = 0.0
        self.pnlpct = 0.0
        self.pnlcomm = 0.0

        self.justopened = False
        self.isopen = False
        self.isclosed = False

        self.baropen = 0
        self.dtopen = 0.0
        self.barclose = 0
        self.dtclose = 0.0
        self.barlen = 0

        self.historyon = historyon
        self.history = list()

        self.status = self.Created

    def __len__(self):
        """Absolute size of the trade"""
        return abs(self.size)

    def __bool__(self):
        """Trade size is not 0"""
        return self.size != 0

    __nonzero__ = __bool__

    def getdataname(self):
        """Shortcut to retrieve the name of the data this trade references"""
        return self.data._name

    def open_datetime(self, tz=None, naive=True):
"""Returns a datetime.datetime object with the datetime in which
the trade was opened

Args::
    tz: (Default value = None)
    naive: (Default value = True)"""
    naive: (Default value = True)"""
        return self.data.num2date(self.dtopen, tz=tz, naive=naive)

    def close_datetime(self, tz=None, naive=True):
"""Returns a datetime.datetime object with the datetime in which
the trade was closed

Args::
    tz: (Default value = None)
    naive: (Default value = True)"""
    naive: (Default value = True)"""
        return self.data.num2date(self.dtclose, tz=tz, naive=naive)

    def update(self, order, size, price, value, commission, pnl, comminfo):
"""Updates the current trade. The logic does not check if the
trade is reversed, which is not conceptually supported by the
object.
If an update sets the size attribute to 0, "closed" will be
set to true
Updates may be received twice for each order, once for the existing
size which has been closed (sell undoing a buy) and a second time for
the the opening part (sell reversing a buy)

Args::
    order: the order object which has (completely or partially)
    size: amount to update the order
    price: always be positive to ensure consistency
    value: (unused) cost incurred in new size/price op
    commission: incurred commission in the new size/price op
    pnl: (unused) generated by the executed part
    comminfo:"""
    comminfo:"""
        if not size:
            return  # empty update, skip all other calculations

        # Commission can only increase
        self.commission += commission

        # Update size and keep a reference for logic an calculations
        oldsize = self.size
        self.size += size  # size will carry the opposite sign if reducing

        # Check if it has been currently opened
        self.justopened = bool(not oldsize and size)

        if self.justopened:
            self.baropen = len(self.data)
            self.dtopen = 0.0 if order.p.simulated else self.data.datetime[0]
            self.long = self.size > 0

        # Any size means the trade was opened
        self.isopen = bool(self.size)

        # Update current trade length
        self.barlen = len(self.data) - self.baropen

        # record if the position was closed (set to null)
        self.isclosed = bool(oldsize and not self.size)

        # record last bar for the trade
        if self.isclosed:
            self.isopen = False
            self.barclose = len(self.data)
            self.dtclose = self.data.datetime[0]

            self.status = self.Closed
        elif self.isopen:
            self.status = self.Open

        if abs(self.size) > abs(oldsize):
            # position increased (be it positive or negative)
            # update the average price
            self.price = (oldsize * self.price + size * price) / self.size
            pnl = 0.0
            self._pnlentrysum += self.price * abs(self.size)

        else:  # abs(self.size) < abs(oldsize)
            # position reduced/closed
            pnl = comminfo.profitandloss(-size, self.price, price)

        self.pnl += pnl
        self.pnlcomm = self.pnl - self.commission
        self.pnlpct = self.pnl / self._pnlentrysum

        self.value = comminfo.getvaluesize(self.size, self.price)

        # Update the history if needed
        if self.historyon:
            dt0 = self.data.datetime[0] if not order.p.simulated else 0.0
            histentry = TradeHistory(
                self.status,
                dt0,
                self.barlen,
                self.size,
                self.price,
                self.value,
                self.pnl,
                self.pnlcomm,
                self.data._tz,
            )
            histentry.doupdate(order, size, price, commission)
            self.history.append(histentry)
