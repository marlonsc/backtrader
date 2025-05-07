"""testcommon.py module.

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

import datetime
import os
import os.path
import sys

import backtrader as bt
import backtrader.utils.flushfile
from backtrader.metabase import ParamsBase

# append module root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

modpath = os.path.dirname(os.path.abspath(__file__))
dataspath = "../datas"
datafiles = [
    "2006-day-001.txt",
    "2006-week-001.txt",
]

DATAFEED = bt.feeds.BacktraderCSVData

FROMDATE = datetime.datetime(2006, 1, 1)
TODATE = datetime.datetime(2006, 12, 31)


def getdatadir(filename):
"""Args::
    filename:"""
"""Args::
    index: 
    fromdate: (Default value = FROMDATE)
    todate: (Default value = TODATE)"""
    todate: (Default value = TODATE)"""

    datapath = getdatadir(datafiles[index])
    data = DATAFEED(dataname=datapath, fromdate=fromdate, todate=todate)

    return data


def runtest(
    datas,
    strategy,
    runonce=None,
    preload=None,
    exbar=None,
    plot=False,
    optimize=False,
    maxcpus=1,
    writer=None,
    analyzer=None,
    **kwargs,
):
"""Args::
    datas: 
    strategy: 
    runonce: (Default value = None)
    preload: (Default value = None)
    exbar: (Default value = None)
    plot: (Default value = False)
    optimize: (Default value = False)
    maxcpus: (Default value = 1)
    writer: (Default value = None)
    analyzer: (Default value = None)"""
    analyzer: (Default value = None)"""

    runonces = [True, False] if runonce is None else [runonce]
    preloads = [True, False] if preload is None else [preload]
    exbars = [-2, -1, False] if exbar is None else [exbar]

    cerebros = list()
    for prload in preloads:
        for ronce in runonces:
            for exbar in exbars:
                cerebro = bt.Cerebro(
                    runonce=ronce,
                    preload=prload,
                    maxcpus=maxcpus,
                    exactbars=exbar,
                )

                if kwargs.get("main", False):
                    print("prload {} / ronce {} exbar {}".format(prload, ronce, exbar))

                if isinstance(datas, bt.LineSeries):
                    datas = [datas]
                for data in datas:
                    cerebro.adddata(data)

                if not optimize:
                    cerebro.addstrategy(strategy, **kwargs)

                    if writer:
                        wr = writer[0]
                        wrkwargs = writer[1]
                        cerebro.addwriter(wr, **wrkwargs)

                    if analyzer:
                        al = analyzer[0]
                        alkwargs = analyzer[1]
                        cerebro.addanalyzer(al, **alkwargs)

                else:
                    cerebro.optstrategy(strategy, **kwargs)

                cerebro.run()
                if plot:
                    cerebro.plot()

                cerebros.append(cerebro)

    return cerebros


class TestStrategy(bt.Strategy):
""""""
""""""
""""""
""""""
""""""
""""""
""""""
"""This class is used as base for tests that check the proper
    handling of meta parameters like `frompackages`, `packages`, `params`, `lines`
    in inherited classes"""
    """

    frompackages = (("math", "factorial"),)

    def __init__(self):
""""""
        self.range = factorial(10)
