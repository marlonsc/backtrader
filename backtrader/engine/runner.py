# Copyright (c) 2025 backtrader contributors
"""
Lógica de execução e orquestração do loop principal do backtrader.
Todas as funções e docstrings devem ser line-wrap ≤ 90 caracteres.
"""

import itertools
import multiprocessing
from backtrader.utils.optreturn import OptReturn
from backtrader.observers.broker import Broker
from backtrader.observers.buysell import BuySell
from backtrader.observers.trades import Trades
from backtrader.observers.trades import DataTrades


def startrun(cerebro):
    """
    Inicia a execução das estratégias, incluindo otimização se necessário.
    :param cerebro: Instância de Cerebro
    """
    iterstrats = itertools.product(*cerebro.strats)
    dooptimize = getattr(cerebro, "_dooptimize", False)
    maxcpus = getattr(cerebro.p, "maxcpus", 1)
    predata = getattr(cerebro.p, "predata", False)
    if not dooptimize or maxcpus == 1:
        # Se não for otimização ou só 1 núcleo, executa sequencial
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
    Finaliza a execução das estratégias, retornando os resultados.
    :param cerebro: Instância de Cerebro
    """
    dooptimize = getattr(cerebro, "_dooptimize", False)
    if not dooptimize:
        # evitar lista de listas para casos regulares
        return cerebro.runstrats[0]
    return cerebro.runstrats


def runstrategies(cerebro, iterstrat, predata=False):
    """
    Executa o loop principal das estratégias.
    :param cerebro: Instância de Cerebro
    :param iterstrat: Iterador de estratégias
    :param predata: Flag de pré-carregamento
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
    Executa o pré-processamento das estratégias antes do loop principal.
    :param cerebro: Instância de Cerebro
    :param iterstrat: Iterador de estratégias
    :param predata: Flag de pré-carregamento
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
    Executa o kernel principal das estratégias (placeholder para extensões futuras).
    :param cerebro: Instância de Cerebro
    """
    # Placeholder: implementar lógica específica se necessário
    pass


def _runnext(cerebro, runstrats):
    """
    Executa o loop de execução "next" para as estratégias.
    :param cerebro: Instância de Cerebro
    :param runstrats: Lista de estratégias em execução
    """
    # Implementação extraída de cerebro.py
    for strat in runstrats:
        while not strat.stop():
            strat.next()


def _runonce(cerebro, runstrats):
    """
    Executa o loop de execução "runonce" para as estratégias.
    :param cerebro: Instância de Cerebro
    :param runstrats: Lista de estratégias em execução
    """
    # Implementação extraída de cerebro.py
    for strat in runstrats:
        strat.runonce()
