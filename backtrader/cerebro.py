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

import collections
import datetime
import itertools

try:  # For new Python versions
    # collections.Iterable -> collections.abc.Iterable
    collectionsAbc = collections.abc
except AttributeError:  # For old Python versions
    collectionsAbc = collections  # Используем collections.Iterable


from . import indicator, linebuffer
from .brokers.bbroker import BackBroker
from .engine.runner import (
    _runnext,
    _runonce,
    finishrun,
    prerunstrategies,
    runstrategies,
    runstrategieskenel,
    startrun,
)
from .feeds.chainer import Chainer
from .feeds.rollover import RollOver
from .metabase import MetaParams
from .plot.plot import Plot_OldSync
from .strategy import SignalStrategy, Strategy
from .utils.calendar import addcalendar, addtz
from .utils.iter import iterize
from .utils.params import make_params
from .utils.py3 import (
    map,
    with_metaclass,
    zip,
)
from .utils.timer import notify_timer, schedule_timer
from .writer import WriterFile

# Defined here to make it pickable. Ideally it could be defined inside Cerebro


class Cerebro(with_metaclass(MetaParams, object)):
    """ """

    params = (
        ("preload", True),
        ("predata", False),
        ("runonce", True),
        ("maxcpus", None),
        ("stdstats", True),
        ("oldbuysell", False),
        ("oldtrades", False),
        ("lookahead", 0),
        ("exactbars", False),
        ("optdatas", True),
        ("optreturn", True),
        ("objcache", False),
        ("live", False),
        ("writer", False),
        ("tradehistory", False),
        ("oldsync", False),
        ("tz", None),
        ("cheat_on_open", False),
        ("broker_coo", True),
        ("quicknotify", False),
        ("bar_on_exit", True),
    )

    def __init__(self):
        self.p = None  # Ensures self.p exists before any access
        # Ensures self.params is always a list of tuples
        params_iter = []
        if hasattr(self, "params"):
            if isinstance(self.params, (list, tuple)):
                params_iter = self.params
            elif hasattr(self.params, "_getitems"):
                params_iter = list(self.params._getitems())
        if self.p is None:
            self.p = make_params(params_iter)
        # Ensures that all expected parameters exist
        for pname, pval in params_iter:
            if not hasattr(self.p, pname):
                setattr(self.p, pname, pval)
        self._dolive = False
        self._doreplay = False
        self._dooptimize = False
        self.stores = list()
        self.feeds = list()
        self.datas = list()
        self.datasbyname = collections.OrderedDict()
        self.strats = list()
        self.optcbs = list()  # Holds a list of callbacks for opt strategies
        self.observers = list()
        self.analyzers = list()
        self.indicators = list()
        self.sizers = dict()
        self.writers = list()
        self.storecbs = list()
        self.datacbs = list()
        self.signals = list()
        self.listeners = list()
        self._signal_strat = (None, None, None)
        self._signal_concurrent = False
        self._signal_accumulate = False
        self._dataid = itertools.count(1)
        self._broker = BackBroker()
        self._broker.cerebro = self
        self._tradingcal = None  # TradingCalendar()
        self._pretimers = list()
        self._ohistory = list()
        self._fhistory = None
        self._optcount = 1
        self.runningstrats = list()

    def set_fund_history(self, fund):
        """Add a history of orders to be directly executed in the broker for
        performance evaluation

          - ``fund``: is an iterable (ex: list, tuple, iterator, generator)
            in which each element will be also an iterable (with length) with
            the following sub-elements (2 formats are possible)

            ``[datetime, share_value, net asset value]``

            **Note**: it must be sorted (or produce sorted elements) by
              datetime ascending

            where:

              - ``datetime`` is a python ``date/datetime`` instance or a string
                with format YYYY-MM-DD[THH:MM:SS[.us]] where the elements in
                brackets are optional
              - ``share_value`` is an float/integer
              - ``net_asset_value`` is a float/integer

        :param fund:

        """
        self._fhistory = fund

    def add_order_history(self, orders, notify=True):
        """Add a history of orders to be directly executed in the broker for
        performance evaluation

          - ``orders``: is an iterable (ex: list, tuple, iterator, generator)
            in which each element will be also an iterable (with length) with
            the following sub-elements (2 formats are possible)

            ``[datetime, size, price]`` or ``[datetime, size, price, data]``

            **Note**: it must be sorted (or produce sorted elements) by
              datetime ascending

            where:

              - ``datetime`` is a python ``date/datetime`` instance or a string
                with format YYYY-MM-DD[THH:MM:SS[.us]] where the elements in
                brackets are optional
              - ``size`` is an integer (positive to *buy*, negative to *sell*)
              - ``price`` is a float/integer
              - ``data`` if present can take any of the following values

                - *None* - The 1st data feed will be used as target
                - *integer* - The data with that index (insertion order in
                  **Cerebro**) will be used
                - *string* - a data with that name, assigned for example with
                  ``cerebro.addata(data, name=value)``, will be the target

          - ``notify`` (default: *True*)

            If ``True`` the 1st strategy inserted in the system will be
            notified of the artificial orders created following the information
            from each order in ``orders``

        **Note**: Implicit in the description is the need to add a data feed
          which is the target of the orders. This is for example needed by
          analyzers which track for example the returns

        :param orders:
        :param notify:  (Default value = True)

        """
        self._ohistory.append((orders, notify))

    def notify_timer(self, timer, when, *args, **kwargs):
        """Delegation to timer notification utility."""
        notify_timer(timer, when, *args, **kwargs)

    def add_timer(
        self,
        when,
        offset=datetime.timedelta(),
        repeat=datetime.timedelta(),
        weekdays=None,
        weekcarry=False,
        monthdays=None,
        monthcarry=True,
        allow=None,
        tzdata=None,
        strats=False,
        cheat=False,
        *args,
        **kwargs,
    ):
        """Schedules a timer using utility."""
        return schedule_timer(
            self,
            when,
            offset=offset,
            repeat=repeat,
            weekdays=weekdays,
            weekcarry=weekcarry,
            monthdays=monthdays,
            monthcarry=monthcarry,
            allow=allow,
            tzdata=tzdata,
            strats=strats,
            cheat=cheat,
            *args,
            **kwargs,
        )

    def addtz(self, tz):
        """Sets the global timezone using utility."""
        addtz(self.p, tz)

    def addcalendar(self, cal):
        """Adds a global calendar using utility."""
        self._tradingcal = addcalendar(cal)

    def add_signal(self, sigtype, sigcls, *sigargs, **sigkwargs):
        """Adds a signal to the system which will be later added to a
        ``SignalStrategy``

        :param sigtype:
        :param sigcls:
        :param *sigargs:
        :param **sigkwargs:

        """
        self.signals.append((sigtype, sigcls, sigargs, sigkwargs))

    def signal_strategy(self, stratcls, *args, **kwargs):
        """Adds a SignalStrategy subclass which can accept signals

        :param stratcls:
        :param *args:
        :param **kwargs:

        """
        self._signal_strat = (stratcls, args, kwargs)

    def signal_concurrent(self, onoff):
        """If signals are added to the system and the ``concurrent`` value is
        set to True, concurrent orders will be allowed

        :param onoff:

        """
        self._signal_concurrent = onoff

    def signal_accumulate(self, onoff):
        """If signals are added to the system and the ``accumulate`` value is
        set to True, entering the market when already in the market, will be
        allowed to increase a position

        :param onoff:

        """
        self._signal_accumulate = onoff

    def addstore(self, store):
        """Adds an ``Store`` instance to the if not already present

        :param store:

        """
        if store not in self.stores:
            self.stores.append(store)

    def addwriter(self, wrtcls, *args, **kwargs):
        """Adds an ``Writer`` class to the mix. Instantiation will be done at
        ``run`` time in cerebro

        :param wrtcls:
        :param *args:
        :param **kwargs:

        """
        self.writers.append((wrtcls, args, kwargs))

    def addlistener(self, lstcls, *args, **kwargs):
        """

        :param lstcls:
        :param *args:
        :param **kwargs:

        """
        self.listeners.append((lstcls, args, kwargs))

    def addsizer(self, sizercls, *args, **kwargs):
        """Adds a ``Sizer`` class (and args) which is the default sizer for any
        strategy added to cerebro

        :param sizercls:
        :param *args:
        :param **kwargs:

        """
        self.sizers[None] = (sizercls, args, kwargs)

    def addsizer_byidx(self, idx, sizercls, *args, **kwargs):
        """Adds a ``Sizer`` class by idx. This idx is a reference compatible to
        the one returned by ``addstrategy``. Only the strategy referenced by
        ``idx`` will receive this size

        :param idx:
        :param sizercls:
        :param *args:
        :param **kwargs:

        """
        self.sizers[idx] = (sizercls, args, kwargs)

    def addindicator(self, indcls, *args, **kwargs):
        """Adds an ``Indicator`` class to the mix. Instantiation will be done at
        ``run`` time in the passed strategies

        :param indcls:
        :param *args:
        :param **kwargs:

        """
        self.indicators.append((indcls, args, kwargs))

    def addanalyzer(self, ancls, *args, **kwargs):
        """Adds an ``Analyzer`` class to the mix. Instantiation will be done at
        ``run`` time

        :param ancls:
        :param *args:
        :param **kwargs:

        """
        self.analyzers.append((ancls, args, kwargs))

    def addobserver(self, obscls, *args, **kwargs):
        """Adds an ``Observer`` class to the mix. Instantiation will be done at
        ``run`` time

        :param obscls:
        :param *args:
        :param **kwargs:

        """
        self.observers.append((False, obscls, args, kwargs))

    def addobservermulti(self, obscls, *args, **kwargs):
        """Adds an ``Observer`` class to the mix. Instantiation will be done at
        ``run`` time

        It will be added once per "data" in the system. A use case is a
        buy/sell observer which observes individual datas.

        A counter-example is the CashValue, which observes system-wide values

        :param obscls:
        :param *args:
        :param **kwargs:

        """
        self.observers.append((True, obscls, args, kwargs))

    def addstorecb(self, callback):
        """Adds a callback to get messages which would be handled by the
        notify_store method

        The signature of the callback must support the following:

          - callback(msg, *args, **kwargs)

        The actual ``msg``, ``*args`` and ``**kwargs`` received are
        implementation defined (depend entirely on the *data/broker/store*) but
        in general one should expect them to be *printable* to allow for
        reception and experimentation.

        :param callback:

        """
        self.storecbs.append(callback)

    def _notify_store(self, msg, *args, **kwargs):
        """

        :param msg:
        :param *args:
        :param **kwargs:

        """
        for callback in self.storecbs:
            callback(msg, *args, **kwargs)

        self.notify_store(msg, *args, **kwargs)

    def notify_store(self, msg, *args, **kwargs):
        """Receive store notifications in cerebro

        This method can be overridden in ``Cerebro`` subclasses

        The actual ``msg``, ``*args`` and ``**kwargs`` received are
        implementation defined (depend entirely on the *data/broker/store*) but
        in general one should expect them to be *printable* to allow for
        reception and experimentation.

        :param msg:
        :param *args:
        :param **kwargs:

        """

    def _storenotify(self):
        """ """
        for store in self.stores:
            for notif in store.get_notifications():
                msg, args, kwargs = notif

                self._notify_store(msg, *args, **kwargs)
                for strat in self.runningstrats:
                    strat.notify_store(msg, *args, **kwargs)

    def adddatacb(self, callback):
        """Adds a callback to get messages which would be handled by the
        notify_data method

        The signature of the callback must support the following:

          - callback(data, status, *args, **kwargs)

        The actual ``*args`` and ``**kwargs`` received are implementation
        defined (depend entirely on the *data/broker/store*) but in general one
        should expect them to be *printable* to allow for reception and
        experimentation.

        :param callback:

        """
        self.datacbs.append(callback)

    def _datanotify(self):
        """ """
        for data in self.datas:
            for notif in data.get_notifications():
                status, args, kwargs = notif
                self._notify_data(data, status, *args, **kwargs)
                for strat in self.runningstrats:
                    strat.notify_data(data, status, *args, **kwargs)

    def _notify_data(self, data, status, *args, **kwargs):
        """

        :param data:
        :param status:
        :param *args:
        :param **kwargs:

        """
        for callback in self.datacbs:
            callback(data, status, *args, **kwargs)

        self.notify_data(data, status, *args, **kwargs)

    def notify_data(self, data, status, *args, **kwargs):
        """Receive data notifications in cerebro

        This method can be overridden in ``Cerebro`` subclasses

        The actual ``*args`` and ``**kwargs`` received are
        implementation defined (depend entirely on the *data/broker/store*) but
        in general one should expect them to be *printable* to allow for
        reception and experimentation.

        :param data:
        :param status:
        :param *args:
        :param **kwargs:

        """

    def adddata(self, data, name=None):
        """Adds a ``Data Feed`` instance to the mix.

        If ``name`` is not None it will be put into ``data._name`` which is
        meant for decoration/plotting purposes.

        :param data:
        :param name:  (Default value = None)

        """
        if name is not None:
            data._name = name

        data._id = next(self._dataid)
        data.setenvironment(self)

        self.datas.append(data)
        self.datasbyname[data._name] = data
        feed = data.getfeed()
        if feed and feed not in self.feeds:
            self.feeds.append(feed)

        if data.islive():
            self._dolive = True

        return data

    def chaindata(self, *args, **kwargs):
        """Chains several data feeds into one

        If ``name`` is passed as named argument and is not None it will be put
        into ``data._name`` which is meant for decoration/plotting purposes.

        If ``None``, then the name of the 1st data will be used

        :param *args:
        :param **kwargs:

        """
        dname = kwargs.pop("name", None)
        if dname is None:
            dname = args[0]._dataname
        d = Chainer(*args)
        self.adddata(d, name=dname)
        return d

    def rolloverdata(self, *args, **kwargs):
        """Chains several data feeds into one

        If ``name`` is passed as named argument and is not None it will be put
        into ``data._name`` which is meant for decoration/plotting purposes.

        If ``None``, then the name of the 1st data will be used

        Any other kwargs will be passed to the RollOver class

        :param *args:
        :param **kwargs:

        """
        dname = kwargs.pop("name", None)
        if dname is None:
            dname = args[0]._dataname
        d = RollOver(*args, **kwargs)
        self.adddata(d, name=dname)
        return d

    def replaydata(self, dataname, name=None, **kwargs):
        """Adds a ``Data Feed`` to be replayed by the system

        If ``name`` is not None it will be put into ``data._name`` which is
        meant for decoration/plotting purposes.

        Any other kwargs like ``timeframe``, ``compression``, ``todate`` which
        are supported by the replay filter will be passed transparently

        :param dataname:
        :param name:  (Default value = None)
        :param **kwargs:

        """
        if any(dataname is x for x in self.datas):
            dataname = dataname.clone()

        dataname.replay(**kwargs)
        self.adddata(dataname, name=name)
        self._doreplay = True

        return dataname

    def resampledata(self, dataname, name=None, **kwargs):
        """Adds a ``Data Feed`` to be resample by the system

        If ``name`` is not None it will be put into ``data._name`` which is
        meant for decoration/plotting purposes.

        Any other kwargs like ``timeframe``, ``compression``, ``todate`` which
        are supported by the resample filter will be passed transparently

        :param dataname:
        :param name:  (Default value = None)
        :param **kwargs:

        """
        if any(dataname is x for x in self.datas):
            dataname = dataname.clone()

        dataname.resample(**kwargs)
        self.adddata(dataname, name=name)
        self._doreplay = True

        return dataname

    def optcallback(self, cb):
        """Adds a *callback* to the list of callbacks that will be called with the
        optimizations when each of the strategies has been run

        The signature: cb(strategy)

        :param cb:

        """
        self.optcbs.append(cb)

    def optstrategy(self, strategy, *args, **kwargs):
        """Adds a ``Strategy`` class to the mix for optimization. Instantiation
        will happen during ``run`` time.

        args and kwargs MUST BE iterables which hold the values to check.

        Example: if a Strategy accepts a parameter ``period``, for optimization
        purposes the call to ``optstrategy`` looks like:

          - cerebro.optstrategy(MyStrategy, period=(15, 25))

        This will execute an optimization for values 15 and 25. Whereas

          - cerebro.optstrategy(MyStrategy, period=range(15, 25))

        will execute MyStrategy with ``period`` values 15 -> 25 (25 not
        included, because ranges are semi-open in Python)

        If a parameter is passed but shall not be optimized the call looks
        like:

          - cerebro.optstrategy(MyStrategy, period=(15,))

        Notice that ``period`` is still passed as an iterable ... of just 1
        element

        ``backtrader`` will anyhow try to identify situations like:

          - cerebro.optstrategy(MyStrategy, period=15)

        and will create an internal pseudo-iterable if possible

        :param strategy:
        :param *args:
        :param **kwargs:

        """

        def add_optcount(params):
            """

            :param params:

            """
            for p in params if isinstance(params, list) else params.values():
                # not everything here might be iterable and count towards
                # optcount (like e.g. bools)
                if not isinstance(p, collections.abc.Iterable):
                    continue
                self._optcount *= len(p)

        self._dooptimize = True
        args = iterize(args)
        optargs = itertools.product(*args)
        add_optcount(args)

        optkeys = list(kwargs)
        add_optcount(kwargs)

        vals = iterize(kwargs.values())
        optvals = itertools.product(*vals)

        okwargs1 = map(zip, itertools.repeat(optkeys), optvals)

        optkwargs = map(dict, okwargs1)

        it = itertools.product([strategy], optargs, optkwargs)
        self.strats.append(it)

    def addstrategy(self, strategy, *args, **kwargs):
        """Adds a ``Strategy`` class to the mix for a single pass run.
        Instantiation will happen during ``run`` time.

        args and kwargs will be passed to the strategy as they are during
        instantiation.

        Returns the index with which addition of other objects (like sizers)
        can be referenced

        :param strategy:
        :param *args:
        :param **kwargs:

        """
        self.strats.append([(strategy, args, kwargs)])
        return len(self.strats) - 1

    def setbroker(self, broker):
        """Sets a specific ``broker`` instance for this strategy, replacing the
        one inherited from cerebro.

        :param broker:

        """
        self._broker = broker
        broker.cerebro = self
        return broker

    def getbroker(self):
        """Returns the broker instance.

        This is also available as a ``property`` by the name ``broker``


        """
        return self._broker

    broker = property(getbroker, setbroker)

    def plot(
        self,
        plotter=None,
        numfigs=1,
        iplot=True,
        start=None,
        end=None,
        width=16,
        height=9,
        dpi=300,
        tight=True,
        use=None,
        **kwargs,
    ):
        """Plots the strategies inside cerebro

        If ``plotter`` is None a default ``Plot`` instance is created and
        ``kwargs`` are passed to it during instantiation.

        ``numfigs`` split the plot in the indicated number of charts reducing
        chart density if wished

        ``iplot``: if ``True`` and running in a ``notebook`` the charts will be
        displayed inline

        ``use``: set it to the name of the desired matplotlib backend. It will
        take precedence over ``iplot``

        ``start``: An index to the datetime line array of the strategy or a
        ``datetime.date``, ``datetime.datetime`` instance indicating the start
        of the plot

        ``end``: An index to the datetime line array of the strategy or a
        ``datetime.date``, ``datetime.datetime`` instance indicating the end
        of the plot

        ``width``: in inches of the saved figure

        ``height``: in inches of the saved figure

        ``dpi``: quality in dots per inches of the saved figure

        ``tight``: only save actual content and not the frame of the figure

        :param plotter:  (Default value = None)
        :param numfigs:  (Default value = 1)
        :param iplot:  (Default value = True)
        :param start:  (Default value = None)
        :param end:  (Default value = None)
        :param width:  (Default value = 16)
        :param height:  (Default value = 9)
        :param dpi:  (Default value = 300)
        :param tight:  (Default value = True)
        :param use:  (Default value = None)
        :param **kwargs:

        """
        # ... rest of the method remains unchanged ...
        if self._exactbars > 0:
            return

        if not plotter:
            plotter = Plot_OldSync(**kwargs)

        # pfillers = {self.datas[i]: self._plotfillers[i]
        # for i, x in enumerate(self._plotfillers)}

        # pfillers2 = {self.datas[i]: self._plotfillers2[i]
        # for i, x in enumerate(self._plotfillers2)}

        figs = []
        for stratlist in self.runstrats:
            for si, strat in enumerate(stratlist):
                rfig = plotter.plot(
                    strat,
                    figid=si * 100,
                    numfigs=numfigs,
                    iplot=iplot,
                    start=start,
                    end=end,
                    use=use,
                )
                # pfillers=pfillers2)

                figs.append(rfig)

            # plotter.show()

        return figs

    def __call__(self, iterstrat):
        """
        Used during optimization to pass the cerebro over the multiprocesing
        module without complains
        """

        predata = (
            getattr(self.p, "optdatas", True) and self._dopreload and self._dorunonce
        )
        return self.runstrategies(iterstrat, predata=predata)

    def __getstate__(self):
        """
        Used during optimization to prevent optimization result `runstrats`
        from being pickled to subprocesses
        Also optcbs don't need to be transfered to subprocesses. They might fail to pickle due to use of e.g. tqdm
        """

        rv = vars(self).copy()
        if "runstrats" in rv:
            del rv["runstrats"]
            del rv["optcbs"]
        return rv

    def runstop(self):
        """If invoked from inside a strategy or anywhere else, including other
        threads the execution will stop as soon as possible."""
        self._event_stop = True  # signal a stop has been requested

    def prerun(self, **kwargs):
        self._event_stop = False  # Stop is requested

        if not self.datas:
            return []  # nothing can be run

        # Ensures that self.params is a Params object
        if not hasattr(self, "params") or not hasattr(self.params, "_getkeys"):
            self.params = self.p
        pkeys = self.params._getkeys() if hasattr(self.params, "_getkeys") else []
        for key, val in kwargs.items():
            if key in pkeys:
                setattr(self.params, key, val)

        # Manage activate/deactivate object cache
        linebuffer.LineActions.cleancache()  # clean cache
        indicator.Indicator.cleancache()  # clean cache

        linebuffer.LineActions.usecache(getattr(self.p, "objcache", False))
        indicator.Indicator.usecache(getattr(self.p, "objcache", False))

        self._dorunonce = getattr(self.p, "runonce", True)
        self._dopreload = getattr(self.p, "preload", True)
        self._exactbars = int(getattr(self.p, "exactbars", 0))

        if self._exactbars:
            self._dorunonce = False  # something is saving memory, no runonce
            self._dopreload = self._dopreload and self._exactbars < 1

        self._doreplay = self._doreplay or any(x.replaying for x in self.datas)
        if self._doreplay:
            # preloading is not supported with replay. full timeframe bars
            # are constructed in realtime
            self._dopreload = False

        if self._dolive or getattr(self.p, "live", False):
            # in this case both preload and runonce must be off
            self._dorunonce = False
            self._dopreload = False

        self.runwriters = list()

        # Add the system default writer if requested
        if getattr(self.p, "writer", False) is True:
            wr = WriterFile()
            self.runwriters.append(wr)

        # Instantiate any other writers
        for wrcls, wrargs, wrkwargs in self.writers:
            wr = wrcls(*wrargs, **wrkwargs)
            self.runwriters.append(wr)

        # Write down if any writer wants the full csv output
        self.writers_csv = any(map(lambda x: x.p.csv, self.runwriters))

        self.runstrats = list()

        if self.signals:  # allow processing of signals
            signalst, sargs, skwargs = self._signal_strat
            if signalst is None:
                # Try to see if the 1st regular strategy is a signal strategy
                try:
                    signalst, sargs, skwargs = self.strats.pop(0)
                except IndexError:
                    pass  # Nothing there
                else:
                    if not isinstance(signalst, SignalStrategy):
                        # no signal ... reinsert at the beginning
                        self.strats.insert(0, (signalst, sargs, skwargs))
                        signalst = None  # flag as not presetn

            if signalst is None:  # recheck
                # Still None, create a default one
                signalst, sargs, skwargs = SignalStrategy, tuple(), dict()

            # Add the signal strategy
            self.addstrategy(
                signalst,
                _accumulate=self._signal_accumulate,
                _concurrent=self._signal_concurrent,
                signals=self.signals,
                *sargs,
                **skwargs,
            )

        if not self.strats:  # Datas are present, add a strategy
            self.addstrategy(Strategy)

    def startrun(self):
        return startrun(self)

    def finishrun(self):
        return finishrun(self)

    def runstrategies(self, iterstrat, predata=False):
        return runstrategies(self, iterstrat, predata=predata)

    def prerunstrategies(self, iterstrat, predata=False):
        return prerunstrategies(self, iterstrat, predata=predata)

    def runstrategieskenel(self):
        return runstrategieskenel(self)

    def _runnext(self, runstrats):
        return _runnext(self, runstrats)

    def _runonce(self, runstrats):
        return _runonce(self, runstrats)

    def _init_stcount(self):
        self.stcount = itertools.count(0)

    def _next_stid(self):
        return next(self.stcount)

    def _brokernotify(self):
        """
        Internal method which kicks the broker and delivers any broker
        notification to the strategy
        """
        self._broker.next()
        while True:
            order = self._broker.get_notification()
            if order is None:
                break

            owner = order.owner
            if owner is None:
                owner = self.runningstrats[0]  # default

            owner._addnotification(
                order, quicknotify=getattr(self.p, "quicknotify", False)
            )

    def get_opt_runcount(self):
        return self._optcount
