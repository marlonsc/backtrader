"""test_bbroker_try_exec_limit.py module.

Description of the module functionality."""

# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
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

import os
import time

try:
    time_clock = time.process_time
except BaseException:
    time_clock = time.clock

import backtrader as bt


class SlipTestStrategy(bt.SignalStrategy):
""""""
"""Args::
    txt: 
    dt: (Default value = None)
    nodate: (Default value = False)"""
    nodate: (Default value = False)"""
        if not nodate:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print("%s, %s" % (dt.isoformat(), txt))
        else:
            print("---------- %s" % (txt))

    def notify_order(self, order):
"""Args::
    order:"""
""""""
""""""
""""""
""""""
""""""
"""Test a fix in bbroker. See backtrader2 pr#22

Args::
    main: (Default value = False)"""
    main: (Default value = False)"""

    cerebro = bt.Cerebro()

    if main:
        strat_kwargs = dict(printdata=True, printops=True)
    else:
        strat_kwargs = dict(printdata=False, printops=False)

    cerebro.addstrategy(SlipTestStrategy, **strat_kwargs)

    cerebro.broker.setcash(10000.0)

    modpath = os.path.dirname(os.path.abspath(__file__))
    dataspath = "../datas"
    datafile = "bbroker_try_exec_limit.txt"
    datapath = os.path.join(modpath, dataspath, datafile)
    data0 = bt.feeds.GenericCSVData(
        dataname=datapath,
        dtformat="%Y-%m-%d",
        timeframe=bt.TimeFrame.Days,
        compression=1,
    )
    cerebro.adddata(data0)

    # Slippage/expected sell executed price
    expected_results = (
        (0, 1297.5),
        (3, 1294.50),
        (4, 1293.50),
        (5, 1293.10),
        (10, 1293.10),
    )

    for expected_result in expected_results:
        cerebro.broker.set_slippage_fixed(expected_result[0])
        strat = cerebro.run()
        if main:
            print(
                "Slippage {}, Sell Executed {:.2f}, Expected price {:.2f}".format(
                    expected_result[0],
                    float(strat[0].sellexec[0]),
                    expected_result[1],
                )
            )

        assert float(strat[0].sellexec[0]) == expected_result[1]


if __name__ == "__main__":
    test_run(main=True)
