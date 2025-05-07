#!/usr/bin389/env python
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
import copy
import datetime
import itertools
import operator

import backtrader as bt
from .order import Order
from .sizers.fixedsize import FixedSize

from .lineiterator import LineIterator, StrategyBase
from .lineroot import (
    LineSingle,
)
from .lineseries import LineSeriesStub
from .trade import Trade
from .utils.autodict import AutoOrderedDict
from .utils.py3 import (
    MAXINT,
    filter,
    iteritems,
    keys,
    map,
    string_types,
    with_metaclass,
)

try:
    from .metastrategy import MetaStrategy
except ImportError:

    class MetaStrategy(type):
        pass


class Strategy(with_metaclass(MetaStrategy, StrategyBase)):
    """Base class to be subclassed for user defined strategies."""

    _ltype = LineIterator.StratType

    csv = True
    _oldsync = False  # update clock using old methodology : data 0

    # keep the latest delivered data date in the line
    lines = ("datetime",)

    def __init__(self, *args, **kwargs):
        super(Strategy, self).__init__(*args, **kwargs)
        self._orderspending = []
        self._tradespending = []
        self._tradehistoryon = False
        self._minperiods = []
        self._minperstatus = 0
        self._dlens = []
        self.indobscsv = []
        self._sizer = None

    def qbuffer(self, savemem=0, replaying=False):
        """Enable the memory saving schemes. Possible values for ``savemem``:
0: No savings. Each lines object keeps in memory all values
1: All lines objects save memory, using the strictly minimum needed
Negative values are meant to be used when plotting is required:
-1: Indicators at Strategy Level and Observers do not enable memory
savings (but anything declared below it does)
-2: Same as -1 plus activation of memory saving for any indicators
which has declared *plotinfo.plot* as False (will not be plotted)

Args:
    savemem: (Default value = 0)
    replaying: (Default value = False)"""
        if savemem < 0:
            # Get any attribute which labels itself as Indicator
            for ind in self._lineiterators[self.IndType]:
                subsave = isinstance(ind, (LineSingle,))
                if not subsave and savemem < -1:
                    subsave = not ind.plotinfo.plot
                ind.qbuffer(savemem=subsave)

        elif savemem > 0:
            for data in self.datas:
                if (
                    not isinstance(data, (str, tuple))
                    and hasattr(data, "qbuffer")
                    and callable(data.qbuffer)
                ):
                    data.qbuffer(replaying=replaying)
            for line in self.lines:
                if (
                    not isinstance(line, (str, tuple))
                    and hasattr(line, "qbuffer")
                    and callable(line.qbuffer)
                ):
                    line.qbuffer(savemem=1)
            # Save in all object types depending on the strategy
            for itcls in self._lineiterators:
                for it in self._lineiterators[itcls]:
                    if (
                        not isinstance(it, (str, tuple))
                        and hasattr(it, "qbuffer")
                        and callable(it.qbuffer)
                    ):
                        it.qbuffer(savemem=1)

    def _periodset(self):
        """ """
        dataids = [id(data) for data in self.datas]

        _dminperiods = collections.defaultdict(list)
        for lineiter in self._lineiterators[LineIterator.IndType]:
            # if multiple datas are used and multiple timeframes the larger
            # timeframe may place larger time constraints in calling next.
            clk = getattr(lineiter, "_clock", None)
            if clk is None:
                clk = getattr(getattr(lineiter, "_owner", None), "_clock", None)
                if clk is None:
                    continue

            while True:
                if id(clk) in dataids:
                    break  # already top-level clock (data feed)

                # See if the current clock has higher level clocks
                clk2 = getattr(clk, "_clock", None)
                if clk2 is None:
                    clk2 = getattr(getattr(clk, "_owner", None), "_clock", None)

                if clk2 is None:
                    break  # if no clock found, bail out

                clk = clk2  # keep the ref and try to go up the hierarchy

            if clk is None:
                continue  # no clock found, go to next

            # LineSeriesStup wraps a line and the clock is the wrapped line and
            # no the wrapper itself.
            if isinstance(clk, LineSeriesStub):
                clk = clk.lines[0]

            _dminperiods[clk].append(lineiter._minperiod)

        self._minperiods = list()
        for data in self.datas:
            # Do not only consider the data as clock but also its lines which
            # may have been individually passed as clock references and
            # discovered as clocks above

            # Initialize with data min period if any
            dlminperiods = _dminperiods[data]

            for l in data.lines:  # search each line for min periods
                if l in _dminperiods:
                    dlminperiods += _dminperiods[l]  # found, add it

            # keep the reference to the line if any was found
            _dminperiods[data] = [max(dlminperiods)] if dlminperiods else []

            dminperiod = max(_dminperiods[data] or [getattr(data, "_minperiod", 0)])
            self._minperiods.append(dminperiod)

        # Set the minperiod
        minperiods = [getattr(x, "_minperiod", 0) for x in self._lineiterators[LineIterator.IndType]]
        self._minperiod = max(minperiods or [getattr(self, "_minperiod", 0)])

    def _addwriter(self, writer):
        """Unlike the other _addxxx functions this one receives an instance
because the writer works at cerebro level and is only passed to the
strategy to simplify the logic

Args:
    writer:"""
        self.writers.append(writer)

    def _addindicator(self, indcls, *indargs, **indkwargs):
        """Args:
    indcls:"""
        indcls(*indargs, **indkwargs)

    def _addanalyzer_slave(self, ancls, *anargs, **ankwargs):
        """Like _addanalyzer but meant for observers (or other entities) which
rely on the output of an analyzer for the data. These analyzers have
not been added by the user and are kept separate from the main
analyzers
Returns the created analyzer

Args:
    ancls:"""
        analyzer = ancls(*anargs, **ankwargs)
        self._slave_analyzers.append(analyzer)
        return analyzer

    def _getanalyzer_slave(self, idx):
        """Args:
    idx:"""
        return self._slave_analyzers.append[idx]

    def _addanalyzer(self, ancls, *anargs, **ankwargs):
        """Args:
    ancls:"""
        anname = ankwargs.pop("_name", "") or ancls.__name__.lower()
        nsuffix = next(self._alnames[anname])
        anname += str(nsuffix or "")  # 0 (first instance) gets no suffix
        analyzer = ancls(*anargs, **ankwargs)
        self.analyzers.append(analyzer, anname)

    def _addobserver(self, multi, obscls, *obsargs, **obskwargs):
        """Args:
    multi: 
    obscls:"""
        obsname = obskwargs.pop("obsname", "")
        if not obsname:
            obsname = obscls.__name__.lower()

        if not multi:
            newargs = list(itertools.chain(self.datas, obsargs))
            obs = obscls(*newargs, **obskwargs)
            self.stats.append(obs, obsname)
            return

        setattr(self.stats, obsname, list())
        l = getattr(self.stats, obsname)

        for data in self.datas:
            obs = obscls(data, *obsargs, **obskwargs)
            l.append(obs)

    def _getminperstatus(self):
        """ """
        # check the min period status connected to datas
        dlens = map(operator.sub, self._minperiods, map(len, self.datas))
        self._minperstatus = minperstatus = max(dlens)
        return minperstatus

    def prenext_open(self):
        """ """

    def nextstart_open(self):
        """ """
        self.next_open()

    def next_open(self):
        """ """

    def _oncepost_open(self):
        """ """
        minperstatus = self._minperstatus
        if minperstatus < 0:
            self.next_open()
        elif minperstatus == 0:
            self.nextstart_open()  # only called for the 1st value
        else:
            self.prenext_open()

    def _oncepost(self, dt):
        """Args:
    dt:"""
        for indicator in self._lineiterators[LineIterator.IndType]:
            if len(indicator._clock) > len(indicator):
                indicator.advance()

        if self._oldsync:
            # Strategy has not been reset, the line is there
            self.advance()
        else:
            # strategy has been reset to beginning. advance step by step
            self.forward()

        self.lines.datetime[0] = dt
        self._notify()

        minperstatus = self._getminperstatus()
        if minperstatus < 0:
            self.next()
        elif minperstatus == 0:
            self.nextstart()  # only called for the 1st value
        else:
            self.prenext()

        self._next_analyzers(minperstatus, once=True)
        self._next_observers(minperstatus, once=True)

        self.clear()

    def _clk_update(self):
        """ """
        if self._oldsync:
            clk_len = super(Strategy, self)._clk_update()
            self.lines.datetime[0] = max(
                d.datetime[0]
                for d in self.datas
                if hasattr(d, "datetime")
                and len(d)
                and not isinstance(d.datetime, (tuple, str))
                and hasattr(d.datetime, "__getitem__")
            )
            return clk_len

        newdlens = [len(d) for d in self.datas]
        if any(nl > l for l, nl in zip(self._dlens, newdlens)):
            self.forward()

        self.lines.datetime[0] = max(
            d.datetime[0]
            for d in self.datas
            if hasattr(d, "datetime")
            and len(d)
            and not isinstance(d.datetime, (tuple, str))
            and hasattr(d.datetime, "__getitem__")
        )
        self._dlens = newdlens

        return len(self)

    def _next_open(self):
        """ """
        minperstatus = self._minperstatus
        if minperstatus < 0:
            self.next_open()
        elif minperstatus == 0:
            self.nextstart_open()  # only called for the 1st value
        else:
            self.prenext_open()

    def _next(self):
        """ """
        super(Strategy, self)._next()

        minperstatus = self._getminperstatus()
        self._next_analyzers(minperstatus)
        self._next_observers(minperstatus)

        self.clear()

    def _next_observers(self, minperstatus, once=False):
        """Args:
    minperstatus: 
    once: (Default value = False)"""
        for observer in self._lineiterators[LineIterator.ObsType]:
            for analyzer in observer._analyzers:
                if minperstatus < 0:
                    analyzer._next()
                elif minperstatus == 0:
                    analyzer._nextstart()  # only called for the 1st value
                else:
                    analyzer._prenext()

            if once:
                if len(self) > len(observer):
                    if self._oldsync:
                        observer.advance()
                    else:
                        observer.forward()

                if minperstatus < 0:
                    observer.next()
                elif minperstatus == 0:
                    observer.nextstart()  # only called for the 1st value
                elif len(observer):
                    observer.prenext()
            else:
                observer._next()

    def _next_analyzers(self, minperstatus, once=False):
        """Args:
    minperstatus: 
    once: (Default value = False)"""
        for analyzer in self.analyzers:
            if minperstatus < 0:
                analyzer._next()
            elif minperstatus == 0:
                analyzer._nextstart()  # only called for the 1st value
            else:
                analyzer._prenext()

    def _settz(self, tz):
        """Args:
    tz:"""
        self.lines.datetime._settz(tz)

    def _start(self):
        """ """
        self._periodset()

        for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
            analyzer._start()

        for obs in self.observers:
            if not isinstance(obs, list):
                obs = [obs]  # support of multi-data observers

            for o in obs:
                o._start()

        # change operators to stage 2
        self._stage2()

        self._dlens = [len(data) for data in self.datas]

        self._minperstatus = MAXINT  # start in prenext

        self.start()

    def start(self):
        """Called right before the backtesting is about to be started."""

    def getwriterheaders(self):
        """ """
        self.indobscsv = [self]

        indobs = itertools.chain(self.getindicators_lines(), self.getobservers())
        self.indobscsv.extend(filter(lambda x: x.csv, indobs))

        headers = list()

        # prepare the indicators/observers data headers
        for iocsv in self.indobscsv:
            name = (
                getattr(getattr(iocsv, "plotinfo", None), "plotname", None)
                or iocsv.__class__.__name__
            )
            headers.append(name)
            headers.append("len")
            if hasattr(iocsv, "getlinealiases"):
                headers.extend(iocsv.getlinealiases())
            else:
                headers.extend([])

        return headers

    def getwritervalues(self):
        """ """
        values = list()

        for iocsv in self.indobscsv:
            name = (
                getattr(getattr(iocsv, "plotinfo", None), "plotname", None)
                or iocsv.__class__.__name__
            )
            values.append(name)
            lio = len(iocsv)
            values.append(lio)
            if (
                lio
                and hasattr(iocsv, "lines")
                and not isinstance(iocsv.lines, (tuple, str))
                and hasattr(iocsv.lines, "itersize")
                and callable(iocsv.lines.itersize)
            ):
                values.extend(map(lambda l: l[0], iocsv.lines.itersize()))
            elif hasattr(iocsv, "lines") and hasattr(iocsv.lines, "size"):
                values.extend([""] * iocsv.lines.size())
            else:
                values.extend([])

        return values

    def getwriterinfo(self):
        """ """
        wrinfo = AutoOrderedDict()

        wrinfo["Params"] = self.p._getkwargs()

        sections = [
            ["Indicators", self.getindicators_lines()],
            ["Observers", self.getobservers()],
        ]

        for sectname, sectitems in sections:
            sinfo = wrinfo[sectname]
            for item in sectitems:
                itname = item.__class__.__name__
                sinfo[itname].Lines = item.lines.getlinealiases() or None
                sinfo[itname].Params = item.p._getkwargs() or None

        ainfo = wrinfo.Analyzers

        # Internal Value Analyzer
        ainfo.Value.Begin = self.broker.startingcash
        ainfo.Value.End = self.broker.getvalue()

        # no slave analyzers for writer
        for aname, analyzer in self.analyzers.getitems():
            ainfo[aname].Params = analyzer.p._getkwargs() or None
            ainfo[aname].Analysis = analyzer.get_analysis()

        return wrinfo

    def _stop(self):
        """ """
        self.stop()

        for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
            analyzer._stop()

        # change operators back to stage 1 - allows reuse of datas
        self._stage1()

    def stop(self):
        """Called right before the backtesting is about to be stopped"""

    def set_tradehistory(self, onoff=True):
        """Args:
    onoff: (Default value = True)"""
        self._tradehistoryon = onoff

    def clear(self):
        """ """
        self._orders.extend(self._orderspending)
        self._orderspending = list()
        self._tradespending = list()

    def _addnotification(self, order, quicknotify=False):
        """Args:
    order: 
    quicknotify: (Default value = False)"""
        if not order.p.simulated:
            self._orderspending.append(order)

        if quicknotify:
            qorders = [order]
            qtrades = []
        else:
            qorders = []
            qtrades = []

        if not order.executed.size:
            if quicknotify:
                self._notify(qorders=qorders, qtrades=qtrades)
            return

        tradedata = order.data._compensate
        if tradedata is None:
            tradedata = order.data

        datatrades = self._trades[tradedata][order.tradeid]
        if not datatrades:
            trade = Trade(
                data=tradedata,
                tradeid=order.tradeid,
                historyon=self._tradehistoryon,
            )
            datatrades.append(trade)
        else:
            trade = datatrades[-1]

        for exbit in order.executed.iterpending():
            if exbit is None:
                break

            if exbit.closed:
                trade.update(
                    order,
                    exbit.closed,
                    exbit.price,
                    exbit.closedvalue,
                    exbit.closedcomm,
                    exbit.pnl,
                    comminfo=order.comminfo,
                )

                if trade.isclosed:
                    self._tradespending.append(copy.copy(trade))
                    if quicknotify:
                        qtrades.append(copy.copy(trade))

            # Update it if needed
            if exbit.opened:
                if trade.isclosed:
                    trade = Trade(
                        data=tradedata,
                        tradeid=order.tradeid,
                        historyon=self._tradehistoryon,
                    )
                    datatrades.append(trade)

                trade.update(
                    order,
                    exbit.opened,
                    exbit.price,
                    exbit.openedvalue,
                    exbit.openedcomm,
                    exbit.pnl,
                    comminfo=order.comminfo,
                )

                # This extra check covers the case in which different tradeid
                # orders have put the position down to 0 and the next order
                # "opens" a position but "closes" the trade
                if trade.isclosed:
                    self._tradespending.append(copy.copy(trade))
                    if quicknotify:
                        qtrades.append(copy.copy(trade))

            if trade.justopened:
                self._tradespending.append(copy.copy(trade))
                if quicknotify:
                    qtrades.append(copy.copy(trade))

        if quicknotify:
            self._notify(qorders=qorders, qtrades=qtrades)

    def _notify(self, qorders=None, qtrades=None):
        """Args:
    qorders: (Default value = None)
    qtrades: (Default value = None)"""
        if qorders is None:
            qorders = []
        if qtrades is None:
            qtrades = []
        if self.cerebro.p.quicknotify:
            procorders = qorders
            proctrades = qtrades
        else:
            procorders = self._orderspending
            proctrades = self._tradespending

        for order in procorders:
            if order.exectype != order.Historical or order.histnotify:
                self.notify_order(order)
            for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
                analyzer._notify_order(order)

        for trade in proctrades:
            self.notify_trade(trade)
            for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
                analyzer._notify_trade(trade)

        if qorders:
            return  # cash is notified on a regular basis

        cash = self.broker.getcash()
        value = self.broker.getvalue()
        fundvalue = self.broker.fundvalue
        fundshares = self.broker.fundshares

        self.notify_cashvalue(cash, value)
        self.notify_fund(cash, value, fundvalue, fundshares)
        for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
            analyzer._notify_cashvalue(cash, value)
            analyzer._notify_fund(cash, value, fundvalue, fundshares)

    def add_timer(
        self,
        when,
        offset=None,
        repeat=None,
        weekdays=None,
        weekcarry=False,
        monthdays=None,
        monthcarry=True,
        allow=None,
        tzdata=None,
        cheat=False,
        *args,
        **kwargs,
    ):
        """**Note**: can be called during ``__init__`` or ``start``
Schedules a timer to invoke either a specified callback or the
``notify_timer`` of one or more strategies.

Args:
    when: can be
    offset: which must be a (Default value = datetime.timedelta())
    repeat: which must be a (Default value = datetime.timedelta())
    weekdays: a (Default value = [])
    weekcarry: default
    monthdays: a (Default value = [])
    monthcarry: default
    allow: default
    tzdata: which can be either (Default value = None)
    cheat: default

Returns:
    - The created timer"""
        if offset is None:
            offset = datetime.timedelta()
        if repeat is None:
            repeat = datetime.timedelta()
        if weekdays is None:
            weekdays = []
        if monthdays is None:
            monthdays = []
        return self.cerebro._add_timer(
            owner=self,
            when=when,
            offset=offset,
            repeat=repeat,
            weekdays=weekdays,
            weekcarry=weekcarry,
            monthdays=monthdays,
            monthcarry=monthcarry,
            allow=allow,
            tzdata=tzdata,
            strats=False,
            cheat=cheat,
            *args,
            **kwargs,
        )

    def notify_timer(self, timer, when, *args, **kwargs):
        """Receives a timer notification where ``timer`` is the timer which was

Args:
    timer: 
    when: 

Returns:
    and ``kwargs`` are any additional arguments passed to ``add_timer``"""

    def notify_cashvalue(self, cash, value):
        """Receives the current fund value, value status of the strategy's broker

Args:
    cash: 
    value:"""

    def notify_fund(self, cash, value, fundvalue, shares):
        """Receives the current cash, value, fundvalue and fund shares

Args:
    cash: 
    value: 
    fundvalue: 
    shares:"""

    def notify_order(self, order):
        """Receives an order whenever there has been a change in one

Args:
    order:"""

    def notify_trade(self, trade):
        """Receives a trade whenever there has been a change in one

Args:
    trade:"""

    def notify_store(self, msg, *args, **kwargs):
        """Receives a notification from a store provider

Args:
    msg:"""

    def notify_data(self, data, status, *args, **kwargs):
        """Receives a notification from data

Args:
    data: 
    status:"""

    def getdatanames(self):
        """Returns a list of the existing data names"""
        return keys(self.env.datasbyname)

    def getdatabyname(self, name):
        """Returns a given data by name using the environment (cerebro)

Args:
    name:"""
        return self.env.datasbyname[name]

    def cancel(self, order):
        """Cancels the order in the broker

Args:
    order:"""
        self.broker.cancel(order)

    def buy(
        self,
        data=None,
        size=None,
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
        """Create a buy (long) order and send it to the broker
- ``data`` (default: ``None``)
For which data the order has to be created. If ``None`` then the
first data in the system, ``self.datas[0] or self.data0`` (aka
``self.data``) will be used
- ``size`` (default: ``None``)
Size to use (positive) of units of data to use for the order.
If ``None`` the ``sizer`` instance retrieved via ``getsizer`` will
be used to determine the size.
- ``price`` (default: ``None``)
Price to use (live brokers may place restrictions on the actual
format if it does not comply to minimum tick size requirements)
``None`` is valid for ``Market`` and ``Close`` orders (the market
determines the price)
For ``Limit``, ``Stop`` and ``StopLimit`` orders this value
determines the trigger point (in the case of ``Limit`` the trigger
is obviously at which price the order should be matched)
- ``plimit`` (default: ``None``)
Only applicable to ``StopLimit`` orders. This is the price at which
to set the implicit *Limit* order, once the *Stop* has been
triggered (for which ``price`` has been used)
- ``trailamount`` (default: ``None``)
If the order type is StopTrail or StopTrailLimit, this is an
absolute amount which determines the distance to the price (below
for a Sell order and above for a buy order) to keep the trailing
stop
- ``trailpercent`` (default: ``None``)
If the order type is StopTrail or StopTrailLimit, this is a
percentage amount which determines the distance to the price (below
for a Sell order and above for a buy order) to keep the trailing
stop (if ``trailamount`` is also specified it will be used)
- ``exectype`` (default: ``None``)
Possible values:
- ``Order.Market`` or ``None``. A market order will be executed
with the next available price. In backtesting it will be the
opening price of the next bar
- ``Order.Limit``. An order which can only be executed at the given
``price`` or better
- ``Order.Stop``. An order which is triggered at ``price`` and
executed like an ``Order.Market`` order
- ``Order.StopLimit``. An order which is triggered at ``price`` and
executed as an implicit *Limit* order with price given by
``pricelimit``
- ``Order.Close``. An order which can only be executed with the
closing price of the session (usually during a closing auction)
- ``Order.StopTrail``. An order which is triggered at ``price``
minus ``trailamount`` (or ``trailpercent``) and which is updated
if the price moves away from the stop
- ``Order.StopTrailLimit``. An order which is triggered at
``price`` minus ``trailamount`` (or ``trailpercent``) and which
is updated if the price moves away from the stop
- ``valid`` (default: ``None``)
Possible values:
- ``None``: this generates an order that will not expire (aka
*Good till cancel*) and remain in the market until matched or
canceled. In reality brokers tend to impose a temporal limit,
but this is usually so far away in time to consider it as not
expiring
- ``datetime.datetime`` or ``datetime.date`` instance: the date
will be used to generate an order valid until the given
datetime (aka *good till date*)
- ``Order.DAY`` or ``0`` or ``timedelta()``: a day valid until
the *End of the Session* (aka *day* order) will be generated
- ``numeric value``: This is assumed to be a value corresponding
to a datetime in ``matplotlib`` coding (the one used by
``backtrader``) and will used to generate an order valid until
that time (*good till date*)
- ``tradeid`` (default: ``0``)
This is an internal value applied by ``backtrader`` to keep track
of overlapping trades on the same asset. This ``tradeid`` is sent
back to the *strategy* when notifying changes to the status of the
orders.
- ``oco`` (default: ``None``)
Another ``order`` instance. This order will become part of an OCO
(Order Cancel Others) group. The execution of one of the orders,
immediately cancels all others in the same group
- ``parent`` (default: ``None``)
Controls the relationship of a group of orders, for example a buy
which is bracketed by a high-side limit sell and a low side stop
sell. The high/low side orders remain inactive until the parent
order has been either executed (they become active) or is
canceled/expires (the children are also canceled) bracket orders
have the same size
- ``transmit`` (default: ``True``)
Indicates if the order has to be **transmitted**, ie: not only
placed in the broker but also issued. This is meant for example to
control bracket orders, in which one disables the transmission for
the parent and 1st set of children and activates it for the last
children, which triggers the full placement of all bracket orders.
- ``**kwargs``: additional broker implementations may support extra

Args:
    data: (Default value = None)
    size: (Default value = None)
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

Returns:
    - the submitted order"""
        if isinstance(data, string_types):
            data = self.getdatabyname(data)

        data = data if data is not None else self.datas[0]
        size = size if size is not None else self.getsizing(data, isbuy=True)

        if size:
            return self.broker.buy(
                self,
                data,
                size=abs(size),
                price=price,
                plimit=plimit,
                exectype=exectype,
                valid=valid,
                tradeid=tradeid,
                oco=oco,
                trailamount=trailamount,
                trailpercent=trailpercent,
                parent=parent,
                transmit=transmit,
                **kwargs,
            )

        return None

    def sell(
        self,
        data=None,
        size=None,
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
        """To create a selll (short) order and send it to the broker

        See the documentation for ``buy`` for an explanation of the parameters

        Returns: the submitted order

        :param data:  (Default value = None)
        :param size:  (Default value = None)
        :param price:  (Default value = None)
        :param plimit:  (Default value = None)
        :param exectype:  (Default value = None)
        :param valid:  (Default value = None)
        :param tradeid:  (Default value = 0)
        :param oco:  (Default value = None)
        :param trailamount:  (Default value = None)
        :param trailpercent:  (Default value = None)
        :param parent:  (Default value = None)
        :param transmit:  (Default value = True)
        :param **kwargs:

        """
        if isinstance(data, string_types):
            data = self.getdatabyname(data)

        data = data if data is not None else self.datas[0]
        size = size if size is not None else self.getsizing(data, isbuy=False)

        if size:
            return self.broker.sell(
                self,
                data,
                size=abs(size),
                price=price,
                plimit=plimit,
                exectype=exectype,
                valid=valid,
                tradeid=tradeid,
                oco=oco,
                trailamount=trailamount,
                trailpercent=trailpercent,
                parent=parent,
                transmit=transmit,
                **kwargs,
            )

        return None

    def close(self, data=None, size=None, **kwargs):
        """Counters a long/short position closing it

        See the documentation for ``buy`` for an explanation of the parameters

        Note:

          - ``size``: automatically calculated from the existing position if
            not provided (default: ``None``) by the caller

        Returns: the submitted order

        :param data:  (Default value = None)
        :param size:  (Default value = None)
        :param **kwargs:

        """
        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        size = abs(size if size is not None else possize)

        if possize > 0:
            return self.sell(data=data, size=size, **kwargs)
        elif possize < 0:
            return self.buy(data=data, size=size, **kwargs)

        return None

    def buy_bracket(
        self,
        data=None,
        size=None,
        price=None,
        plimit=None,
        exectype=Order.Limit,
        valid=None,
        tradeid=0,
        trailamount=None,
        trailpercent=None,
        oargs=None,
        stopprice=None,
        stopexec=Order.Stop,
        stopargs=None,
        limitprice=None,
        limitexec=Order.Limit,
        limitargs=None,
        **kwargs,
    ):
        """Create a bracket order group (low side - buy order - high side). The
default behavior is as follows:
- Issue a **buy** order with execution ``Limit``
- Issue a *low side* bracket **sell** order with execution ``Stop``
- Issue a *high side* bracket **sell** order with execution
``Limit``.
See below for the different parameters
- ``data`` (default: ``None``)
For which data the order has to be created. If ``None`` then the
first data in the system, ``self.datas[0] or self.data0`` (aka
``self.data``) will be used
- ``size`` (default: ``None``)
Size to use (positive) of units of data to use for the order.
If ``None`` the ``sizer`` instance retrieved via ``getsizer`` will
be used to determine the size.
**Note**: The same size is applied to all 3 orders of the bracket
- ``price`` (default: ``None``)
Price to use (live brokers may place restrictions on the actual
format if it does not comply to minimum tick size requirements)
``None`` is valid for ``Market`` and ``Close`` orders (the market
determines the price)
For ``Limit``, ``Stop`` and ``StopLimit`` orders this value
determines the trigger point (in the case of ``Limit`` the trigger
is obviously at which price the order should be matched)
- ``plimit`` (default: ``None``)
Only applicable to ``StopLimit`` orders. This is the price at which
to set the implicit *Limit* order, once the *Stop* has been
triggered (for which ``price`` has been used)
- ``trailamount`` (default: ``None``)
If the order type is StopTrail or StopTrailLimit, this is an
absolute amount which determines the distance to the price (below
for a Sell order and above for a buy order) to keep the trailing
stop
- ``trailpercent`` (default: ``None``)
If the order type is StopTrail or StopTrailLimit, this is a
percentage amount which determines the distance to the price (below
for a Sell order and above for a buy order) to keep the trailing
stop (if ``trailamount`` is also specified it will be used)
- ``exectype`` (default: ``bt.Order.Limit``)
Possible values: (see the documentation for the method ``buy``
- ``valid`` (default: ``None``)
Possible values: (see the documentation for the method ``buy``
- ``tradeid`` (default: ``0``)
Possible values: (see the documentation for the method ``buy``
- ``oargs`` (default: ``{}``)
Specific keyword arguments (in a ``dict``) to pass to the main side
order. Arguments from the default ``**kwargs`` will be applied on
top of this.
- ``**kwargs``: additional broker implementations may support extra

Args:
    data: (Default value = None)
    size: (Default value = None)
    price: (Default value = None)
    plimit: (Default value = None)
    exectype: (Default value = bt.Order.Limit)
    valid: (Default value = None)
    tradeid: (Default value = 0)
    trailamount: (Default value = None)
    trailpercent: (Default value = None)
    oargs: (Default value = {})
    stopprice: default
    stopexec: None (Default value = bt.Order.Stop)
    stopargs: default
    limitprice: default
    limitexec: None (Default value = bt.Order.Limit)
    limitargs: default

Returns:
    - A list containing the 3 orders [order, stop side, limit side]"""
        if oargs is None:
            oargs = {}
        if stopargs is None:
            stopargs = {}
        if limitargs is None:
            limitargs = {}
        kargs = dict(
            size=size,
            data=data,
            price=price,
            plimit=plimit,
            exectype=exectype,
            valid=valid,
            tradeid=tradeid,
            trailamount=trailamount,
            trailpercent=trailpercent,
        )
        kargs.update(oargs)
        kargs.update(kwargs)
        kargs["transmit"] = limitexec is None and stopexec is None
        o = self.buy(**kargs)

        if stopexec is not None:
            # low side / stop
            kargs = dict(
                data=data,
                price=stopprice,
                exectype=stopexec,
                valid=valid,
                tradeid=tradeid,
            )
            kargs.update(stopargs)
            kargs.update(kwargs)
            kargs["parent"] = o
            kargs["transmit"] = limitexec is None
            kargs["size"] = o.size
            ostop = self.sell(**kargs)
        else:
            ostop = None

        if limitexec is not None:
            # high side / limit
            kargs = dict(
                data=data,
                price=limitprice,
                exectype=limitexec,
                valid=valid,
                tradeid=tradeid,
            )
            kargs.update(limitargs)
            kargs.update(kwargs)
            kargs["parent"] = o
            kargs["transmit"] = True
            kargs["size"] = o.size
            olimit = self.sell(**kargs)
        else:
            olimit = None

        return [o, ostop, olimit]

    def sell_bracket(
        self,
        data=None,
        size=None,
        price=None,
        plimit=None,
        exectype=Order.Limit,
        valid=None,
        tradeid=0,
        trailamount=None,
        trailpercent=None,
        oargs=None,
        stopprice=None,
        stopexec=Order.Stop,
        stopargs=None,
        limitprice=None,
        limitexec=Order.Limit,
        limitargs=None,
        **kwargs,
    ):
        """Create a bracket order group (low side - buy order - high side). The
default behavior is as follows:
- Issue a **sell** order with execution ``Limit``
- Issue a *high side* bracket **buy** order with execution ``Stop``
- Issue a *low side* bracket **buy** order with execution ``Limit``.
See ``bracket_buy`` for the meaning of the parameters
High/Low Side orders can be suppressed by using:
- ``stopexec=None`` to suppress the *high side*
- ``limitexec=None`` to suppress the *low side*

Args:
    data: (Default value = None)
    size: (Default value = None)
    price: (Default value = None)
    plimit: (Default value = None)
    exectype: (Default value = bt.Order.Limit)
    valid: (Default value = None)
    tradeid: (Default value = 0)
    trailamount: (Default value = None)
    trailpercent: (Default value = None)
    oargs: (Default value = {})
    stopprice: (Default value = None)
    stopexec: (Default value = bt.Order.Stop)
    stopargs: (Default value = {})
    limitprice: (Default value = None)
    limitexec: (Default value = bt.Order.Limit)
    limitargs: (Default value = {})

Returns:
    - A list containing the 3 orders [order, stop side, limit side]"""
        if oargs is None:
            oargs = {}
        if stopargs is None:
            stopargs = {}
        if limitargs is None:
            limitargs = {}
        kargs = dict(
            size=size,
            data=data,
            price=price,
            plimit=plimit,
            exectype=exectype,
            valid=valid,
            tradeid=tradeid,
            trailamount=trailamount,
            trailpercent=trailpercent,
        )
        kargs.update(oargs)
        kargs.update(kwargs)
        kargs["transmit"] = limitexec is None and stopexec is None
        o = self.sell(**kargs)

        if stopexec is not None:
            # high side / stop
            kargs = dict(
                data=data,
                price=stopprice,
                exectype=stopexec,
                valid=valid,
                tradeid=tradeid,
            )
            kargs.update(stopargs)
            kargs.update(kwargs)
            kargs["parent"] = o
            kargs["transmit"] = limitexec is None
            kargs["size"] = o.size
            ostop = self.buy(**kargs)
        else:
            ostop = None

        if limitexec is not None:
            # low side / limit
            kargs = dict(
                data=data,
                price=limitprice,
                exectype=limitexec,
                valid=valid,
                tradeid=tradeid,
            )
            kargs.update(limitargs)
            kargs.update(kwargs)
            kargs["parent"] = o
            kargs["transmit"] = True
            kargs["size"] = o.size
            olimit = self.buy(**kargs)
        else:
            olimit = None

        return [o, ostop, olimit]

    def order_target_size(self, data=None, target=0, **kwargs):
        """Place an order to rebalance a position to have final size of ``target``
The current ``position`` size is taken into account as the start point
to achieve ``target``
- If ``target`` > ``pos.size`` -> buy ``target - pos.size``
- If ``target`` < ``pos.size`` -> sell ``pos.size - target``
It returns either:
- The generated order
or
- ``None`` if no order has been issued (``target == position.size``)

Args:
    data: (Default value = None)
    target: (Default value = 0)"""
        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        if not target and possize:
            return self.close(data=data, size=possize, **kwargs)

        elif target > possize:
            return self.buy(data=data, size=target - possize, **kwargs)

        elif target < possize:
            return self.sell(data=data, size=possize - target, **kwargs)

        return None  # no execution target == possize

    def order_target_value(self, data=None, target=0.0, price=None, **kwargs):
        """Place an order to rebalance a position to have final value of
``target``
The current ``value`` is taken into account as the start point to
achieve ``target``
- If no ``target`` then close postion on data
- If ``target`` > ``value`` then buy on data
- If ``target`` < ``value`` then sell on data
It returns either:
- The generated order
or
- ``None`` if no order has been issued

Args:
    data: (Default value = None)
    target: (Default value = 0.0)
    price: (Default value = None)"""

        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        if not target and possize:  # closing a position
            return self.close(data=data, size=possize, price=price, **kwargs)

        else:
            value = self.broker.getvalue(datas=[data])
            comminfo = self.broker.getcommissioninfo(data)

            # Make sure a price is there
            price = price if price is not None else data.close[0]

            if target > value:
                size = comminfo.getsize(price, target - value)
                return self.buy(data=data, size=size, price=price, **kwargs)

            elif target < value:
                size = comminfo.getsize(price, value - target)
                return self.sell(data=data, size=size, price=price, **kwargs)

        return None  # no execution size == possize

    def order_target_percent(self, data=None, target=0.0, **kwargs):
        """Place an order to rebalance a position to have final value of
``target`` percentage of current portfolio ``value``
``target`` is expressed in decimal: ``0.05`` -> ``5%``
It uses ``order_target_value`` to execute the order.
Example:
- ``target=0.05`` and portfolio value is ``100``
- The ``value`` to be reached is ``0.05 * 100 = 5``
- ``5`` is passed as the ``target`` value to ``order_target_value``
The current ``value`` is taken into account as the start point to
achieve ``target``
The ``position.size`` is used to determine if a position is ``long`` /
``short``
- If ``target`` > ``value``
- buy if ``pos.size >= 0`` (Increase a long position)
- sell if ``pos.size < 0`` (Increase a short position)
- If ``target`` < ``value``
- sell if ``pos.size >= 0`` (Decrease a long position)
- buy if ``pos.size < 0`` (Decrease a short position)
It returns either:
- The generated order
or
- ``None`` if no order has been issued (``target == position.size``)

Args:
    data: (Default value = None)
    target: (Default value = 0.0)"""
        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        self.getposition(data, self.broker).size
        target *= self.broker.getvalue()

        return self.order_target_value(data=data, target=target, **kwargs)

    def getposition(self, data=None, broker=None):
        """Returns the current position for a given data in a given broker.
If both are None, the main data and the default broker will be used
A property ``position`` is also available

Args:
    data: (Default value = None)
    broker: (Default value = None)"""
        data = data if data is not None else self.datas[0]
        broker = broker or self.broker
        return broker.getposition(data)

    position = property(getposition)

    def getpositionbyname(self, name=None, broker=None):
        """Returns the current position for a given name in a given broker.
If both are None, the main data and the default broker will be used
A property ``positionbyname`` is also available

Args:
    name: (Default value = None)
    broker: (Default value = None)"""
        data = self.datas[0] if not name else self.getdatabyname(name)
        broker = broker or self.broker
        return broker.getposition(data)

    positionbyname = property(getpositionbyname)

    def getpositions(self, broker=None):
        """Returns the current by data positions directly from the broker
If the given ``broker`` is None, the default broker will be used
A property ``positions`` is also available

Args:
    broker: (Default value = None)"""
        broker = broker or self.broker
        return broker.positions

    positions = property(getpositions)

    def getpositionsbyname(self, broker=None):
        """Returns the current by name positions directly from the broker
If the given ``broker`` is None, the default broker will be used
A property ``positionsbyname`` is also available

Args:
    broker: (Default value = None)"""
        broker = broker or self.broker
        positions = broker.positions

        posbyname = collections.OrderedDict()
        for name, data in iteritems(self.env.datasbyname):
            posbyname[name] = positions[data]

        return posbyname

    positionsbyname = property(getpositionsbyname)

    def _addsizer(self, sizer, *args, **kwargs):
        """Args:
    sizer:"""
        if sizer is None:
            self.setsizer(FixedSize())
        else:
            self.setsizer(sizer, *args, **kwargs)

    def setsizer(self, sizer):
        """Replace the default (fixed stake) sizer

Args:
    sizer:"""
        self._sizer = sizer
        sizer.set(self, self.broker)
        return sizer

    def getsizer(self):
        """Returns the sizer which is in used if automatic statke calculation is
used
Also available as ``sizer``"""
        return self._sizer

    sizer = property(getsizer, setsizer)

    def getsizing(self, data=None, isbuy=True):
        """Args:
    data: (Default value = None)
    isbuy: (Default value = True)

Returns:
    situation"""
        data = data if data is not None else self.datas[0]
        return self._sizer.getsizing(data, isbuy=isbuy)
