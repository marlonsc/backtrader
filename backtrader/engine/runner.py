# Copyright (c) 2025 backtrader contributors
"""
Execution logic and orchestration of the main backtrader loop.
All functions and docstrings should be line-wrapped ≤ 90 characters.
"""

import itertools
import multiprocessing

from backtrader.observers.broker import Broker
from backtrader.observers.buysell import BuySell
from backtrader.observers.trades import DataTrades, Trades
from backtrader.utils.optreturn import OptReturn


def startrun(cerebro):
    """
    Starts the execution of strategies, including optimization if necessary.
    :param cerebro: Cerebro instance
    """
    iterstrats = itertools.product(*cerebro.strats)
    dooptimize = getattr(cerebro, "_dooptimize", False)
    maxcpus = getattr(cerebro.p, "maxcpus", 1)
    predata = getattr(cerebro.p, "predata", False)
    if not dooptimize or maxcpus == 1:
        # If not optimization or only 1 core, execute sequentially
        for iterstrat in iterstrats:
            runstrat = cerebro.runstrategies(iterstrat, predata=predata)
            cerebro.runstrats.append(runstrat)
            if dooptimize:
                for cb in cerebro.optcbs:
                    cb(runstrat)
    else:
        optdatas = getattr(cerebro.p, "optdatas", True)
        dopreload = getattr(cerebro, "_dopreload", False)
        dorunonce = getattr(cerebro, "_dorunonce", False)
        exactbars = getattr(cerebro, "_exactbars", 0)
        if optdatas and dopreload and dorunonce:
            for data in cerebro.datas:
                data.reset()
                if exactbars < 1:
                    data.extend(size=getattr(cerebro.p, "lookahead", 0))
                data._start()
                if dopreload:
                    data.preload()
        pool = multiprocessing.Pool(maxcpus or None)
        for r in pool.imap(cerebro, iterstrats):
            cerebro.runstrats.append(r)
            for cb in cerebro.optcbs:
                cb(r)
        pool.close()
        if optdatas and dopreload and dorunonce:
            for data in cerebro.datas:
                data.stop()


def finishrun(cerebro):
    """
    Finalizes the execution of strategies, returning the results.
    :param cerebro: Cerebro instance
    """
    dooptimize = getattr(cerebro, "_dooptimize", False)
    if not dooptimize:
        # avoid list of lists for regular cases
        return cerebro.runstrats[0]
    return cerebro.runstrats


def runstrategies(cerebro, iterstrat, predata=False):
    """
    Executes the main loop of strategies.
    :param cerebro: Cerebro instance
    :param iterstrat: Strategy iterator
    :param predata: Pre-loading flag
    """
    cerebro._init_stcount()
    cerebro.runningstrats = runstrats = list()
    for store in cerebro.stores:
        store.start()
    if getattr(cerebro.p, "cheat_on_open", False) and getattr(
        cerebro.p, "broker_coo", True
    ):
        if hasattr(cerebro._broker, "set_coo"):
            cerebro._broker.set_coo(True)
    if cerebro._fhistory is not None:
        cerebro._broker.set_fund_history(cerebro._fhistory)
    for orders, onotify in cerebro._ohistory:
        cerebro._broker.add_order_history(orders, onotify)
    cerebro._broker.start()
    for feed in cerebro.feeds:
        feed.start()
    if getattr(cerebro, "writers_csv", False):
        wheaders = list()
        for data in cerebro.datas:
            if getattr(data, "csv", False):
                wheaders.extend(data.getwriterheaders())
        for writer in getattr(cerebro, "runwriters", []):
            if getattr(writer.p, "csv", False):
                writer.addheaders(wheaders)
    if not predata:
        for data in cerebro.datas:
            data.reset()
            if getattr(cerebro, "_exactbars", 0) < 1:
                data.extend(size=getattr(cerebro.p, "lookahead", 0))
            data._start()
            if getattr(cerebro, "_dopreload", False):
                data.preload()
    for stratcls, sargs, skwargs in iterstrat:
        sargs = cerebro.datas + list(sargs)
        try:
            strat = stratcls(*sargs, **skwargs)
        except Exception:
            continue  # do not add strategy to the mix
        if getattr(cerebro.p, "oldsync", False):
            strat._oldsync = True
        if getattr(cerebro.p, "tradehistory", False):
            strat.set_tradehistory()
        runstrats.append(strat)
    tz = getattr(cerebro.p, "tz", None)
    if isinstance(tz, int):
        tz = cerebro.datas[tz]._tz
    else:
        from backtrader.utils.date import tzparse

        tz = tzparse(tz)
    if runstrats:
        defaultsizer = cerebro.sizers.get(None, (None, None, None))
        for idx, strat in enumerate(runstrats):
            if getattr(cerebro.p, "stdstats", True):
                strat._addobserver(False, Broker)
                if getattr(cerebro.p, "oldbuysell", False):
                    strat._addobserver(True, BuySell)
                else:
                    strat._addobserver(True, BuySell, barplot=True)
                if getattr(cerebro.p, "oldtrades", False) or len(cerebro.datas) == 1:
                    strat._addobserver(False, Trades)
                else:
                    strat._addobserver(False, DataTrades)
            for multi, obscls, obsargs, obskwargs in cerebro.observers:
                strat._addobserver(multi, obscls, *obsargs, **obskwargs)
            for indcls, indargs, indkwargs in cerebro.indicators:
                strat._addindicator(indcls, *indargs, **indkwargs)
            for ancls, anargs, ankwargs in cerebro.analyzers:
                strat._addanalyzer(ancls, *anargs, **ankwargs)
            sizer, sargs, skwargs = cerebro.sizers.get(idx, defaultsizer)
            if sizer is not None:
                strat._addsizer(sizer, *sargs, **skwargs)
            strat._settz(tz)
            strat._start()
            for writer in getattr(cerebro, "runwriters", []):
                if getattr(writer.p, "csv", False):
                    writer.addheaders(strat.getwriterheaders())
        if not predata:
            for strat in runstrats:
                strat.qbuffer(
                    getattr(cerebro, "_exactbars", 0),
                    replaying=getattr(cerebro, "_doreplay", False),
                )
        for writer in getattr(cerebro, "runwriters", []):
            writer.start()
        for listener in getattr(cerebro, "runlisteners", []):
            listener.start(cerebro)
        cerebro._timers = []
        cerebro._timerscheat = []
        for timer in cerebro._pretimers:
            timer.start(cerebro.datas[0])
            if getattr(timer.params, "cheat", False):
                cerebro._timerscheat.append(timer)
            else:
                cerebro._timers.append(timer)
        if getattr(cerebro, "_dopreload", False) and getattr(
            cerebro, "_dorunonce", False
        ):
            if getattr(cerebro.p, "oldsync", False):
                cerebro._runonce_old(runstrats)
            else:
                cerebro._runonce(runstrats)
        else:
            if getattr(cerebro.p, "oldsync", False):
                cerebro._runnext_old(runstrats)
            else:
                cerebro._runnext(runstrats)
        for strat in runstrats:
            strat._stop()
    cerebro._broker.stop()
    if not predata:
        for data in cerebro.datas:
            data.stop()
    for feed in cerebro.feeds:
        feed.stop()
    for store in cerebro.stores:
        store.stop()
    if getattr(cerebro, "_dooptimize", False) and getattr(cerebro.p, "optreturn", True):
        results = list()
        for strat in runstrats:
            for a in strat.analyzers:
                a.strategy = None
                a._parent = None
                try:
                    a.optimize()
                except Exception:
                    pass
            oreturn = OptReturn(strat.params, analyzers=strat.analyzers)
            results.append(oreturn)
        return results
    return runstrats


def prerunstrategies(cerebro, iterstrat, predata=False):
    """
    Executes the pre-processing of strategies before the main loop.
    :param cerebro: Cerebro instance
    :param iterstrat: Strategy iterator
    :param predata: Pre-loading flag
    """
    cerebro._init_stcount()
    cerebro.runningstrats = runstrats = list()
    for stratcls, sargs, skwargs in iterstrat:
        sargs = cerebro.datas + list(sargs)
        try:
            strat = stratcls(*sargs, **skwargs)
        except Exception:
            continue  # do not add strategy to the mix
        if getattr(cerebro.p, "oldsync", False):
            strat._oldsync = True
        if getattr(cerebro.p, "tradehistory", False):
            strat.set_tradehistory()
        runstrats.append(strat)
    tz = getattr(cerebro.p, "tz", None)
    if isinstance(tz, int):
        tz = cerebro.datas[tz]._tz
    else:
        from backtrader.utils.date import tzparse

        tz = tzparse(tz)
    if runstrats:
        defaultsizer = cerebro.sizers.get(None, (None, None, None))
        for idx, strat in enumerate(runstrats):
            if getattr(cerebro.p, "stdstats", True):
                strat._addobserver(False, Broker)
                if getattr(cerebro.p, "oldbuysell", False):
                    strat._addobserver(True, BuySell)
                else:
                    strat._addobserver(True, BuySell, barplot=True)
                if getattr(cerebro.p, "oldtrades", False) or len(cerebro.datas) == 1:
                    strat._addobserver(False, Trades)
                else:
                    strat._addobserver(False, DataTrades)
            for multi, obscls, obsargs, obskwargs in cerebro.observers:
                strat._addobserver(multi, obscls, *obsargs, **obskwargs)
            for indcls, indargs, indkwargs in cerebro.indicators:
                strat._addindicator(indcls, *indargs, **indkwargs)
            for ancls, anargs, ankwargs in cerebro.analyzers:
                strat._addanalyzer(ancls, *anargs, **ankwargs)
            sizer, sargs, skwargs = cerebro.sizers.get(idx, defaultsizer)
            if sizer is not None:
                strat._addsizer(sizer, *sargs, **skwargs)
            strat._settz(tz)
            strat._start()
            for writer in getattr(cerebro, "runwriters", []):
                if getattr(writer.p, "csv", False):
                    writer.addheaders(strat.getwriterheaders())
        if not predata:
            for strat in runstrats:
                strat.qbuffer(
                    getattr(cerebro, "_exactbars", 0),
                    replaying=getattr(cerebro, "_doreplay", False),
                )
        for writer in getattr(cerebro, "runwriters", []):
            writer.start()
        for listener in getattr(cerebro, "runlisteners", []):
            listener.start(cerebro)
        cerebro._timers = []
        cerebro._timerscheat = []
        for timer in cerebro._pretimers:
            timer.start(cerebro.datas[0])
            if getattr(timer.params, "cheat", False):
                cerebro._timerscheat.append(timer)
            else:
                cerebro._timers.append(timer)
    return runstrats


def runstrategieskenel(cerebro):
    """
    Executes the main kernel of strategies (placeholder for future extensions).
    :param cerebro: Cerebro instance
    """
    # Placeholder: implement specific logic if needed
    pass


def _runnext(cerebro, runstrats):
    """
    Executes the "next" execution loop for strategies.
    :param cerebro: Cerebro instance
    :param runstrats: List of running strategies
    """
    # Implementation extracted from cerebro.py
    for strat in runstrats:
        while not strat.stop():
            strat.next()


def _runonce(cerebro, runstrats):
    """
    Executes the "runonce" execution loop for strategies.
    :param cerebro: Cerebro instance
    :param runstrats: List of running strategies
    """
    # Implementation extracted from cerebro.py
    for strat in runstrats:
        strat.runonce()
