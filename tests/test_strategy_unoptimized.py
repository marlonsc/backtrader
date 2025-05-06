"""test_strategy_unoptimized.py module.

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

BUYCREATE = [
    "3641.42",
    "3798.46",
    "3874.61",
    "3860.00",
    "3843.08",
    "3648.33",
    "3526.84",
    "3632.93",
    "3788.96",
    "3841.31",
    "4045.22",
    "4052.89",
]

SELLCREATE = [
    "3763.73",
    "3811.45",
    "3823.11",
    "3821.97",
    "3837.86",
    "3604.33",
    "3562.56",
    "3772.21",
    "3780.18",
    "3974.62",
    "4048.16",
]

BUYEXEC = [
    "3643.35",
    "3801.03",
    "3872.37",
    "3863.57",
    "3845.32",
    "3656.43",
    "3542.65",
    "3639.65",
    "3799.86",
    "3840.20",
    "4047.63",
    "4052.55",
]

SELLEXEC = [
    "3763.95",
    "3811.85",
    "3822.35",
    "3822.57",
    "3829.82",
    "3598.58",
    "3545.92",
    "3766.80",
    "3782.15",
    "3979.73",
    "4045.05",
]


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

    def notify_order(self, order):
"""Args::
    order:"""
""""""
""""""
""""""
""""""
"""Args::
    main: (Default value = False)"""
    main: (Default value = False)"""
    for stlike in [False, True]:
        datas = [testcommon.getdata(i) for i in range(chkdatas)]
        testcommon.runtest(
            datas,
            BtTestStrategy,
            printdata=main,
            printops=main,
            stocklike=stlike,
            plot=main,
        )


if __name__ == "__main__":
    test_run(main=True)
