"""test_analyzer-sqn.py module.

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

import time

try:
    time_clock = time.process_time
except BaseException:
    time_clock = time.clock

import backtrader as bt
import backtrader.indicators as btind
import testcommon


class BtTestStrategy(bt.Strategy):
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

    def notify_trade(self, trade):
"""Args::
    trade:"""
"""Args::
    order:"""
""""""
""""""
""""""
""""""
"""Args::
    main: (Default value = False)"""
    main: (Default value = False)"""
    datas = [testcommon.getdata(i) for i in range(chkdatas)]

    for maxtrades in [None, 0, 1]:
        cerebros = testcommon.runtest(
            datas,
            BtTestStrategy,
            printdata=main,
            stocklike=False,
            maxtrades=maxtrades,
            printops=main,
            plot=main,
            analyzer=(bt.analyzers.SQN, {}),
        )

        for cerebro in cerebros:
            strat = cerebro.runstrats[0][0]  # no optimization, only 1
            analyzer = strat.analyzers[0]  # only 1
            analysis = analyzer.get_analysis()
            if main:
                print(analysis)
                print(str(analysis.sqn))
            else:
                if maxtrades == 0 or maxtrades == 1:
                    assert analysis.sqn == 0
                    assert analysis.trades == maxtrades
                else:
                    # Handle different precision
                    assert str(analysis.sqn)[0:14] == "0.912550316439"
                    assert str(analysis.trades) == "11"


if __name__ == "__main__":
    test_run(main=True)
