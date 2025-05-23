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

import argparse
import datetime

import backtrader as bt


class St(bt.Strategy):
    """ """

    params = dict(
        when=bt.timer.SESSION_START,
        timer=True,
        cheat=False,
        offset=datetime.timedelta(),
        repeat=datetime.timedelta(),
        weekdays=[],
        weekcarry=False,
        monthdays=[],
        monthcarry=True,
    )

    def __init__(self):
        """ """
        bt.ind.SMA()
        if self.p.timer:
            self.add_timer(
                when=self.p.when,
                offset=self.p.offset,
                repeat=self.p.repeat,
                weekdays=self.p.weekdays,
                weekcarry=self.p.weekcarry,
                monthdays=self.p.monthdays,
                monthcarry=self.p.monthcarry,
                # tzdata=self.data0,
            )
        if self.p.cheat:
            self.add_timer(
                when=self.p.when,
                offset=self.p.offset,
                repeat=self.p.repeat,
                weekdays=self.p.weekdays,
                weekcarry=self.p.weekcarry,
                monthdays=self.p.monthdays,
                monthcarry=self.p.monthcarry,
                tzdata=self.data0,
                cheat=True,
            )

        self.order = None

    def prenext(self):
        """ """
        self.next()

    def next(self):
        """ """
        _, isowk, isowkday = self.datetime.date().isocalendar()
        txt = "{}, {}, Week {}, Day {}, O {}, H {}, L {}, C {}".format(
            len(self),
            self.datetime.datetime(),
            isowk,
            isowkday,
            self.data.open[0],
            self.data.high[0],
            self.data.low[0],
            self.data.close[0],
        )

        print(txt)

    def notify_timer(self, timer, when, *args, **kwargs):
        """

        :param timer:
        :param when:
        :param *args:
        :param **kwargs:

        """
        print(
            "strategy notify_timer with tid {}, when {} cheat {}".format(
                timer.p.tid, when, timer.p.cheat
            )
        )

        if self.order is None and timer.params.cheat:
            print("-- {} Create buy order".format(self.data.datetime.datetime()))
            self.order = self.buy()

    def notify_order(self, order):
        """

        :param order:

        """
        if order.status == order.Completed:
            print(
                "-- {} Buy Exec @ {}".format(
                    self.data.datetime.datetime(), order.executed.price
                )
            )


def runstrat(args=None):
    """

    :param args:  (Default value = None)

    """
    args = parse_args(args)
    cerebro = bt.Cerebro()

    # Data feed kwargs
    kwargs = dict(
        timeframe=bt.TimeFrame.Minutes,
        compression=5,
        sessionstart=datetime.time(9, 0),
        sessionend=datetime.time(17, 30),
    )

    # Parse from/to-date
    dtfmt, tmfmt = "%Y-%m-%d", "T%H:%M:%S"
    for a, d in ((getattr(args, x), x) for x in ["fromdate", "todate"]):
        if a:
            strpfmt = dtfmt + tmfmt * ("T" in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    # Data feed
    data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **kwargs)
    cerebro.adddata(data0)

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval("dict(" + args.broker + ")"))

    # Sizer
    cerebro.addsizer(bt.sizers.FixedSize, **eval("dict(" + args.sizer + ")"))

    # Strategy
    cerebro.addstrategy(St, **eval("dict(" + args.strat + ")"))

    # Execute
    cerebro.run(**eval("dict(" + args.cerebro + ")"))

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval("dict(" + args.plot + ")"))


def parse_args(pargs=None):
    """

    :param pargs:  (Default value = None)

    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Timer Test Intraday",
    )

    parser.add_argument(
        "--data0",
        default="../../datas/2006-min-005.txt",
        required=False,
        help="Data to read in",
    )

    # Defaults for dates
    parser.add_argument(
        "--fromdate",
        required=False,
        default="",
        help="Date[time] in YYYY-MM-DD[THH:MM:SS] format",
    )

    parser.add_argument(
        "--todate",
        required=False,
        default="",
        help="Date[time] in YYYY-MM-DD[THH:MM:SS] format",
    )

    parser.add_argument(
        "--cerebro",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--broker",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--sizer",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--strat",
        required=False,
        default="",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    parser.add_argument(
        "--plot",
        required=False,
        default="",
        nargs="?",
        const="{}",
        metavar="kwargs",
        help="kwargs in key=value format",
    )

    return parser.parse_args(pargs)


if __name__ == "__main__":
    runstrat()
