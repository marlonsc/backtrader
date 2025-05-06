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
"""
btrun.py - Backtrader command-line runner for strategies, analyzers, and data feeds.

This module provides a command-line interface to configure and run backtrader
strategies, analyzers, observers, and data feeds. It supports modular extension
and dynamic loading of user components.
"""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import argparse
import ast
import datetime
import importlib
import inspect
import logging
import random
import string
import sys

from .. import Analyzer, Cerebro, Observer, Strategy, TimeFrame
from .. import analyzers as bt_analyzers
from .. import indicators as bt_indicators
from .. import observers as bt_observers
from .. import signals as bt_signals
from ..feeds import (
    BacktraderCSVData,
    IBData,
    MT4CSVData,
    OandaData,
    SierraChartCSVData,
    VCData,
    VChartCSVData,
    VChartFile,
    YahooFinanceCSVData,
    YahooFinanceData,
)
from ..writer import WriterFile

DATAFORMATS = dict(
    btcsv=BacktraderCSVData,
    vchartcsv=VChartCSVData,
    vcfile=VChartFile,
    sierracsv=SierraChartCSVData,
    mt4csv=MT4CSVData,
    yahoocsv=YahooFinanceCSVData,
    yahoocsv_unreversed=YahooFinanceCSVData,
    yahoo=YahooFinanceData,
)

try:
    DATAFORMATS["vcdata"] = VCData
except AttributeError:
    pass  # no comtypes available

try:
    DATAFORMATS["ibdata"] = (IBData,)
except AttributeError:
    pass  # no ibpy available

try:
    DATAFORMATS["oandadata"] = (OandaData,)
except AttributeError:
    pass  # no oandapy available

TIMEFRAMES = dict(
    microseconds=TimeFrame.MicroSeconds,
    seconds=TimeFrame.Seconds,
    minutes=TimeFrame.Minutes,
    days=TimeFrame.Days,
    weeks=TimeFrame.Weeks,
    months=TimeFrame.Months,
    years=TimeFrame.Years,
)

__all__ = [
    "btrun",
    "setbroker",
    "getdatas",
    "getmodclasses",
    "getmodfunctions",
    "loadmodule",
    "getobjects",
    "getfunctions",
    "parse_args",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


# Helper to safely parse dict-like strings (key1=val1,key2=val2)
def safe_kwargs_parse(s):
    """Safely parse a string of key=value pairs into a dict.

    :param s: 

    """
    if not s.strip():
        return {}
    try:
        # Replace '=' with ':' and wrap in braces to make it a dict literal
        s = s.replace("=", ":")
        return ast.literal_eval("{" + s + "}")
    except Exception as e:  # Acceptable: only parsing user input, not executing logic
        raise ValueError(f"Invalid kwargs string: {s}") from e


def btrun(pargs=""):
    """Run the Backtrader command-line interface with the given arguments.

    :param pargs: Command-line arguments as a string. Defaults to
            "".
    :type pargs: str
    :returns: None
    Side Effects:
        Configures and runs a Backtrader Cerebro instance, loads data, strategies,
        analyzers, observers, and writers as specified by the arguments. May plot
        results or print analyzer output. Exits the process on critical errors.

    """
    args = parse_args(pargs)

    if args.flush:
        pass

    stdstats = not args.nostdstats

    cer_kwargs_str = args.cerebro
    cer_kwargs = safe_kwargs_parse(cer_kwargs_str)
    if "stdstats" not in cer_kwargs:
        cer_kwargs.update(stdstats=stdstats)

    cerebro = Cerebro(**cer_kwargs)

    tfcp = None  # Fix possibly using variable before assignment
    if args.resample is not None or args.replay is not None:
        if args.resample is not None:
            tfcp = args.resample.split(":")
        elif args.replay is not None:
            tfcp = args.replay.split(":")

        # compression may be skipped and it will default to 1
        if len(tfcp) == 1 or tfcp[1] == "":
            tf, cp = tfcp[0], 1
        else:
            tf, cp = tfcp

        cp = int(cp)  # convert any value to int
        tf = TIMEFRAMES.get(tf, None)

    for data in getdatas(args):
        if args.resample is not None:
            cerebro.resampledata(data, timeframe=tf, compression=cp)
        elif args.replay is not None:
            cerebro.replaydata(data, timeframe=tf, compression=cp)
        else:
            cerebro.adddata(data)

    # get and add signals
    signals = getobjects(
        args.signals, bt_indicators.Indicator, bt_signals, issignal=True
    )
    for sig, kwargs, sigtype in signals:
        stype = getattr(bt_signals, "SIGNAL_" + sigtype.upper())
        cerebro.add_signal(stype, sig, **kwargs)

    # get and add strategies
    strategies = getobjects(args.strategies, Strategy, bt_signals)
    for strat, kwargs in strategies:
        cerebro.addstrategy(strat, **kwargs)

    inds = getobjects(args.indicators, bt_indicators.Indicator, bt_indicators)
    for ind, kwargs in inds:
        cerebro.addindicator(ind, **kwargs)

    obs = getobjects(args.observers, Observer, bt_observers)
    for ob, kwargs in obs:
        cerebro.addobserver(ob, **kwargs)

    ans = getobjects(args.analyzers, Analyzer, bt_analyzers)
    for an, kwargs in ans:
        cerebro.addanalyzer(an, **kwargs)

    setbroker(args, cerebro)

    for wrkwargs_str in args.writers or []:
        wrkwargs = safe_kwargs_parse(wrkwargs_str)
        cerebro.addwriter(WriterFile, **wrkwargs)

    ans = getfunctions(args.hooks, Cerebro)
    for hook, kwargs in ans:
        hook(cerebro, **kwargs)
    runsts = cerebro.run()  # pylint: disable=no-member
    runst = runsts[0]  # single strategy and no optimization

    if args.pranalyzer or args.ppranalyzer:
        if runst.analyzers:
            logger.info("====================\n== Analyzers\n====================")
            for name, analyzer in runst.analyzers.getitems():
                if args.pranalyzer:
                    analyzer.print()
                elif args.ppranalyzer:
                    logger.info("##########\n%s\n##########", name)
                    analyzer.pprint()

    if args.plot:
        pkwargs = dict(style="bar")
        if args.plot is not True:
            # evaluates to True but is not "True" - args were passed
            ekwargs = safe_kwargs_parse(args.plot)
            pkwargs.update(ekwargs)

        # cerebro.plot(numfigs=args.plotfigs, style=args.plotstyle)
        cerebro.plot(**pkwargs)


def setbroker(args, cerebro):
    """Configure the broker instance in Cerebro with cash, commission, margin, and
    slippage settings from the parsed arguments.

    :param args: Parsed command-line arguments.
    :param cerebro: The Backtrader Cerebro instance to configure.
    :returns: None
    Side Effects:
        Modifies the broker state in the Cerebro instance.

    """
    broker = cerebro.getbroker()

    if args.cash is not None:
        broker.setcash(args.cash)

    commkwargs = dict()
    if args.commission is not None:
        commkwargs["commission"] = args.commission
    if args.margin is not None:
        commkwargs["margin"] = args.margin
    if args.mult is not None:
        commkwargs["mult"] = args.mult
    if args.interest is not None:
        commkwargs["interest"] = args.interest
    if args.interest_long is not None:
        commkwargs["interest_long"] = args.interest_long

    if commkwargs:
        broker.setcommission(**commkwargs)

    if args.slip_perc is not None:
        cerebro.broker.set_slippage_perc(
            args.slip_perc,
            slip_open=args.slip_open,
            slip_match=not args.no_slip_match,
            slip_out=args.slip_out,
        )
    elif args.slip_fixed is not None:
        cerebro.broker.set_slippage_fixed(
            args.slip_fixed,
            slip_open=args.slip_open,
            slip_match=not args.no_slip_match,
            slip_out=args.slip_out,
        )


def getdatas(args):
    """Create and return a list of Backtrader data feed objects based on the parsed
    arguments.
    
    Args:

    :param args: 
    :returns: list: List of Backtrader data feed objects.
    
    Side Effects:
        Instantiates data feed objects, may parse dates from arguments.

    """
    # Get the data feed class from the global dictionary
    dfcls = DATAFORMATS[args.format]

    # Prepare some args
    dfkwargs = dict()
    if args.format == "yahoo_unreversed":
        dfkwargs["reverse"] = True

    fmtstr = "%Y-%m-%d"
    if args.fromdate:
        dtsplit = args.fromdate.split("T")
        if len(dtsplit) > 1:
            fmtstr += "T%H:%M:%S"

        fromdate = datetime.datetime.strptime(args.fromdate, fmtstr)
        dfkwargs["fromdate"] = fromdate

    fmtstr = "%Y-%m-%d"
    if args.todate:
        dtsplit = args.todate.split("T")
        if len(dtsplit) > 1:
            fmtstr += "T%H:%M:%S"
        todate = datetime.datetime.strptime(args.todate, fmtstr)
        dfkwargs["todate"] = todate

    if args.timeframe is not None:
        dfkwargs["timeframe"] = TIMEFRAMES[args.timeframe]

    if args.compression is not None:
        dfkwargs["compression"] = args.compression

    datas = list()
    for dname in args.data:
        dfkwargs["dataname"] = dname
        data = dfcls(**dfkwargs)
        datas.append(data)

    return datas


def getmodclasses(mod, clstype, clsname=None):
    """Retrieve classes of a given type from a module, optionally filtering by class
    name.

    :param mod: The module to search for classes.
    :param clstype: The base class type to match.
    :param clsname: Specific class name to match. Defaults to None.
    :type clsname: str
    :returns: List of matching class objects.
    :rtype: list

    """
    clsmembers = inspect.getmembers(mod, inspect.isclass)

    clslist = list()
    for name, cls in clsmembers:
        if not issubclass(cls, clstype):
            continue

        if clsname:
            if clsname == name:
                clslist.append(cls)
                break
        else:
            clslist.append(cls)

    return clslist


def getmodfunctions(mod, funcname=None):
    """Retrieve functions or methods from a module, optionally filtering by function
    name.

    :param mod: The module to search for functions.
    :param funcname: Specific function name to match. Defaults to None.
    :type funcname: str
    :returns: List of matching function or method objects.
    :rtype: list

    """
    members = inspect.getmembers(mod, inspect.isfunction) + inspect.getmembers(
        mod, inspect.ismethod
    )

    funclist = list()
    for name, member in members:
        if funcname:
            if name == funcname:
                funclist.append(member)
                break
        else:
            funclist.append(member)

    return funclist


def loadmodule(modpath, modname=""):
    """Dynamically load a Python module from a file path, optionally with a given
    module name.

    :param modpath: Path to the module file.
    :type modpath: str
    :param modname: Name to assign to the loaded module. Defaults to
            "".
    :type modname: str
    :returns: (module object or None, exception or None)
    :rtype: tuple

    """
    if not modpath.endswith(".py"):
        modpath += ".py"
    if not modname:
        chars = string.ascii_uppercase + string.digits
        modname = "".join(random.choice(chars) for _ in range(10))
    try:
        spec = importlib.util.spec_from_file_location(modname, modpath)
        if spec is None:
            return None, ImportError(f"Cannot create spec for {modpath}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, None
    except Exception as e:
        return None, e


def getobjects(iterable, clsbase, modbase, issignal=False):
    """Load and instantiate objects (classes) from modules or built-in modules,
    optionally handling signal types.

    :param iterable: List of module/class/kwargs specifiers.
    :type iterable: list
    :param clsbase: Base class type to match.
    :param modbase: Default module to use if not specified.
    :param issignal: Whether to handle signal type parsing.
            Defaults to False.
    :type issignal: bool
    :returns: List of (class, kwargs) or (class, kwargs, sigtype) tuples.
    :rtype: list

    """
    retobjects = list()

    for item in iterable or []:
        if issignal:
            sigtokens = item.split("+", 1)
            if len(sigtokens) == 1:  # no + seen
                sigtype = "longshort"
            else:
                sigtype, item = sigtokens

        tokens = item.split(":", 1)

        if len(tokens) == 1:
            modpath = tokens[0]
            name = ""
            kwargs = dict()
        else:
            modpath, name = tokens
            kwtokens = name.split(":", 1)
            if len(kwtokens) == 1:
                # no '(' found
                kwargs = dict()
            else:
                name = kwtokens[0]
                kwtext = safe_kwargs_parse(kwtokens[1])
                kwargs = kwtext

        if modpath:
            mod, e = loadmodule(modpath)

            if not mod:
                logger.error("Failed to load module %s: %s", modpath, e)
                sys.exit(1)
        else:
            mod = modbase

        loaded = getmodclasses(mod=mod, clstype=clsbase, clsname=name)

        if not loaded:
            logger.error("No class %s / module %s", str(name), modpath)
            sys.exit(1)

        if issignal:
            retobjects.append((loaded[0], kwargs, sigtype))
        else:
            retobjects.append((loaded[0], kwargs))

    return retobjects


def getfunctions(iterable, modbase):
    """Load and return functions from modules or built-in modules.

    :param iterable: List of module/function/kwargs specifiers.
    :type iterable: list
    :param modbase: Default module to use if not specified.
    :returns: List of (function, kwargs) tuples.
    :rtype: list

    """
    retfunctions = list()

    for item in iterable or []:
        tokens = item.split(":", 1)

        if len(tokens) == 1:
            modpath = tokens[0]
            name = ""
            kwargs = dict()
        else:
            modpath, name = tokens
            kwtokens = name.split(":", 1)
            if len(kwtokens) == 1:
                # no '(' found
                kwargs = dict()
            else:
                name = kwtokens[0]
                kwtext = safe_kwargs_parse(kwtokens[1])
                kwargs = kwtext

        if modpath:
            mod, e = loadmodule(modpath)

            if not mod:
                logger.error("Failed to load module %s: %s", modpath, e)
                sys.exit(1)
        else:
            mod = modbase

        loaded = getmodfunctions(mod=mod, funcname=name)

        if not loaded:
            logger.error("No function %s / module %s", str(name), modpath)
            sys.exit(1)

        retfunctions.append((loaded[0], kwargs))

    return retfunctions


def parse_args(pargs=""):
    """Parse command-line arguments for the Backtrader runner.

    :param pargs: Arguments as a string. Defaults to "".
    :type pargs: str
    :returns: Parsed arguments namespace.
    :rtype: argparse.Namespace

    """
    parser = argparse.ArgumentParser(
        description="Backtrader Run Script",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    group = parser.add_argument_group(title="Data options")
    # Data options
    group.add_argument(
        "--data",
        "-d",
        action="append",
        required=True,
        help="Data files to be added to the system",
    )

    group = parser.add_argument_group(title="Cerebro options")
    group.add_argument(
        "--cerebro",
        "-cer",
        metavar="kwargs",
        required=False,
        const="",
        default="",
        nargs="?",
        help=(
            "The argument can be specified with the following form:\n"
            "\n"
            "  - kwargs\n"
            "\n"
            '    Example: "preload=True" which set its to True\n'
            "\n"
            "The passed kwargs will be passed directly to the cerebro\n"
            "instance created for the execution\n"
            "\n"
            "The available kwargs to cerebro are:\n"
            "  - preload (default: True)\n"
            "  - runonce (default: True)\n"
            "  - maxcpus (default: None)\n"
            "  - stdstats (default: True)\n"
            "  - live (default: False)\n"
            "  - exactbars (default: False)\n"
            "  - preload (default: True)\n"
            "  - writer (default False)\n"
            "  - oldbuysell (default False)\n"
            "  - tradehistory (default False)\n"
        ),
    )

    group.add_argument(
        "--nostdstats",
        action="store_true",
        help="Disable the standard statistics observers",
    )

    datakeys = list(DATAFORMATS)
    group.add_argument(
        "--format",
        "--csvformat",
        "-c",
        required=False,
        default="btcsv",
        choices=datakeys,
        help="CSV Format",
    )

    group.add_argument(
        "--fromdate",
        "-f",
        required=False,
        default=None,
        help="Starting date in YYYY-MM-DD[THH:MM:SS] format",
    )

    group.add_argument(
        "--todate",
        "-t",
        required=False,
        default=None,
        help="Ending date in YYYY-MM-DD[THH:MM:SS] format",
    )

    group.add_argument(
        "--timeframe",
        "-tf",
        required=False,
        default="days",
        choices=TIMEFRAMES.keys(),
        help="Ending date in YYYY-MM-DD[THH:MM:SS] format",
    )

    group.add_argument(
        "--compression",
        "-cp",
        required=False,
        default=1,
        type=int,
        help="Ending date in YYYY-MM-DD[THH:MM:SS] format",
    )

    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument(
        "--resample",
        "-rs",
        required=False,
        default=None,
        help="resample with timeframe:compression values",
    )

    group.add_argument(
        "--replay",
        "-rp",
        required=False,
        default=None,
        help="replay with timeframe:compression values",
    )

    group.add_argument(
        "--hook",
        dest="hooks",
        action="append",
        required=False,
        metavar="module:hookfunction:kwargs",
        help=(
            "This option can be specified multiple times.\n"
            "\n"
            "The argument can be specified with the following form:\n"
            "\n"
            "  - module:hookfunction:kwargs\n"
            "\n"
            "    Example: mymod:myhook:a=1,b=2\n"
            "\n"
            "kwargs is optional\n"
            "\n"
            "If module is omitted then hookfunction will be sought\n"
            "as the built-in cerebro method. Example:\n"
            "\n"
            "  - :addtz:tz=America/St_Johns\n"
            "\n"
            "If name is omitted, then the 1st function found in the\n"
            "mod will be used. Such as in:\n"
            "\n"
            "  - module or module::kwargs\n"
            "\n"
            "The function specified will be called, with cerebro\n"
            "instance passed as the first argument together with\n"
            "kwargs, if any were specified. This allows to customize\n"
            "cerebro, beyond options provided by this script\n\n"
        ),
    )

    # Module where to read the strategy from
    group = parser.add_argument_group(title="Strategy options")
    group.add_argument(
        "--strategy",
        "-st",
        dest="strategies",
        action="append",
        required=False,
        metavar="module:name:kwargs",
        help=(
            "This option can be specified multiple times.\n"
            "\n"
            "The argument can be specified with the following form:\n"
            "\n"
            "  - module:classname:kwargs\n"
            "\n"
            "    Example: mymod:myclass:a=1,b=2\n"
            "\n"
            "kwargs is optional\n"
            "\n"
            "If module is omitted then class name will be sought in\n"
            "the built-in strategies module. Such as in:\n"
            "\n"
            "  - :name:kwargs or :name\n"
            "\n"
            "If name is omitted, then the 1st strategy found in the mod\n"
            "will be used. Such as in:\n"
            "\n"
            "  - module or module::kwargs"
        ),
    )

    # Module where to read the strategy from
    group = parser.add_argument_group(title="Signals")
    group.add_argument(
        "--signal",
        "-sig",
        dest="signals",
        action="append",
        required=False,
        metavar="module:signaltype:name:kwargs",
        help=(
            "This option can be specified multiple times.\n"
            "\n"
            "The argument can be specified with the following form:\n"
            "\n"
            "  - signaltype:module:signaltype:classname:kwargs\n"
            "\n"
            "    Example: longshort+mymod:myclass:a=1,b=2\n"
            "\n"
            "signaltype may be ommited: longshort will be used\n"
            "\n"
            "    Example: mymod:myclass:a=1,b=2\n"
            "\n"
            "kwargs is optional\n"
            "\n"
            "signaltype will be uppercased to match the defintions\n"
            "fromt the backtrader.signal module\n"
            "\n"
            "If module is omitted then class name will be sought in\n"
            "the built-in signals module. Such as in:\n"
            "\n"
            "  - LONGSHORT::name:kwargs or :name\n"
            "\n"
            "If name is omitted, then the 1st signal found in the mod\n"
            "will be used. Such as in:\n"
            "\n"
            "  - module or module:::kwargs"
        ),
    )

    # Observers
    group = parser.add_argument_group(title="Observers and statistics")
    group.add_argument(
        "--observer",
        "-ob",
        dest="observers",
        action="append",
        required=False,
        metavar="module:name:kwargs",
        help=(
            "This option can be specified multiple times.\n"
            "\n"
            "The argument can be specified with the following form:\n"
            "\n"
            "  - module:classname:kwargs\n"
            "\n"
            "    Example: mymod:myclass:a=1,b=2\n"
            "\n"
            "kwargs is optional\n"
            "\n"
            "If module is omitted then class name will be sought in\n"
            "the built-in observers module. Such as in:\n"
            "\n"
            "  - :name:kwargs or :name\n"
            "\n"
            "If name is omitted, then the 1st observer found in the\n"
            "will be used. Such as in:\n"
            "\n"
            "  - module or module::kwargs"
        ),
    )
    # Analyzers
    group = parser.add_argument_group(title="Analyzers")
    group.add_argument(
        "--analyzer",
        "-an",
        dest="analyzers",
        action="append",
        required=False,
        metavar="module:name:kwargs",
        help=(
            "This option can be specified multiple times.\n"
            "\n"
            "The argument can be specified with the following form:\n"
            "\n"
            "  - module:classname:kwargs\n"
            "\n"
            "    Example: mymod:myclass:a=1,b=2\n"
            "\n"
            "kwargs is optional\n"
            "\n"
            "If module is omitted then class name will be sought in\n"
            "the built-in analyzers module. Such as in:\n"
            "\n"
            "  - :name:kwargs or :name\n"
            "\n"
            "If name is omitted, then the 1st analyzer found in the\n"
            "will be used. Such as in:\n"
            "\n"
            "  - module or module::kwargs"
        ),
    )

    # Analyzer - Print
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--pranalyzer",
        "-pralyzer",
        required=False,
        action="store_true",
        help="Automatically print analyzers",
    )

    group.add_argument(
        "--ppranalyzer",
        "-ppralyzer",
        required=False,
        action="store_true",
        help="Automatically PRETTY print analyzers",
    )

    # Indicators
    group = parser.add_argument_group(title="Indicators")
    group.add_argument(
        "--indicator",
        "-ind",
        dest="indicators",
        metavar="module:name:kwargs",
        action="append",
        required=False,
        help=(
            "This option can be specified multiple times.\n"
            "\n"
            "The argument can be specified with the following form:\n"
            "\n"
            "  - module:classname:kwargs\n"
            "\n"
            "    Example: mymod:myclass:a=1,b=2\n"
            "\n"
            "kwargs is optional\n"
            "\n"
            "If module is omitted then class name will be sought in\n"
            "the built-in analyzers module. Such as in:\n"
            "\n"
            "  - :name:kwargs or :name\n"
            "\n"
            "If name is omitted, then the 1st analyzer found in the\n"
            "will be used. Such as in:\n"
            "\n"
            "  - module or module::kwargs"
        ),
    )

    # Writer
    group = parser.add_argument_group(title="Writers")
    group.add_argument(
        "--writer",
        "-wr",
        dest="writers",
        metavar="kwargs",
        nargs="?",
        action="append",
        required=False,
        const="",
        help=(
            "This option can be specified multiple times.\n"
            "\n"
            "The argument can be specified with the following form:\n"
            "\n"
            "  - kwargs\n"
            "\n"
            "    Example: a=1,b=2\n"
            "\n"
            "kwargs is optional\n"
            "\n"
            "It creates a system wide writer which outputs run data\n"
            "\n"
            "Please see the documentation for the available kwargs"
        ),
    )

    # Broker/Commissions
    group = parser.add_argument_group(title="Cash and Commission Scheme Args")
    group.add_argument(
        "--cash",
        "-cash",
        required=False,
        type=float,
        help="Cash to set to the broker",
    )
    group.add_argument(
        "--commission",
        "-comm",
        required=False,
        type=float,
        help="Commission value to set",
    )
    group.add_argument(
        "--margin",
        "-marg",
        required=False,
        type=float,
        help="Margin type to set",
    )
    group.add_argument(
        "--mult", "-mul", required=False, type=float, help="Multiplier to use"
    )

    group.add_argument(
        "--interest",
        required=False,
        type=float,
        default=None,
        help="Credit Interest rate to apply (0.0x)",
    )

    group.add_argument(
        "--interest_long",
        action="store_true",
        required=False,
        default=None,
        help="Apply credit interest to long positions",
    )

    group.add_argument(
        "--slip_perc",
        required=False,
        default=None,
        type=float,
        help="Enable slippage with a percentage value",
    )
    group.add_argument(
        "--slip_fixed",
        required=False,
        default=None,
        type=float,
        help="Enable slippage with a fixed point value",
    )

    group.add_argument(
        "--slip_open",
        required=False,
        action="store_true",
        help="enable slippage for when matching opening prices",
    )

    group.add_argument(
        "--no-slip_match",
        required=False,
        action="store_true",
        help=(
            "Disable slip_match, ie: matching capped at \n"
            "high-low if slippage goes over those limits"
        ),
    )
    group.add_argument(
        "--slip_out",
        required=False,
        action="store_true",
        help="with slip_match enabled, match outside high-low",
    )

    # Output flushing
    group.add_argument(
        "--flush",
        required=False,
        action="store_true",
        help="flush the output - useful under win32 systems",
    )

    # Plot options
    parser.add_argument(
        "--plot",
        "-p",
        nargs="?",
        metavar="kwargs",
        default=False,
        const=True,
        required=False,
        help=(
            "Plot the read data applying any kwargs passed\n"
            "\n"
            "For example:\n"
            "\n"
            '  --plot style="candle" (to plot candlesticks)\n'
        ),
    )

    if pargs:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == "__main__":
    btrun()
