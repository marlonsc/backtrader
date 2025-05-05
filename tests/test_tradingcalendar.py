#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime

from testcommon import getdatadir
import backtrader as bt
import pytest
import pytz
from util_asserts import assert_data


def _get_trading_calendar(open_hour, close_hour, close_minute):
    cal = bt.TradingCalendar(open=datetime.time(hour=open_hour), close=datetime.time(hour=close_hour, minute=close_minute))
    return cal


def _run_cerebro(use_tcal, open_hour=None, open_minute=None, close_hour=None, close_minute=None):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(bt.strategies.NullStrategy)

    if use_tcal:
        cerebro.addcalendar(_get_trading_calendar(open_hour=open_hour,
                                                  close_hour=close_hour,
                                                  close_minute=close_minute))

    data = bt.feeds.GenericCSVData(
        dataname=getdatadir('ticksample_more.csv'),
        dtformat='%Y-%m-%dT%H:%M:%S.%f',
        timeframe=bt.TimeFrame.Ticks,
    )

    cerebro.resampledata(data, timeframe=bt.TimeFrame.Days, compression=1)

    return cerebro.run()[0]


def test_no_tcal():
    strat = _run_cerebro(use_tcal=False)

    assert len(strat) == 4

    assert_data(strat.data, -3, datetime.datetime(2015, 9, 23, 23, 59, 59, 999989), close=3072)
    assert_data(strat.data, -2, datetime.datetime(2015, 9, 24, 23, 59, 59, 999989), close=3600)
    assert_data(strat.data, -1, datetime.datetime(2015, 9, 25, 23, 59, 59, 999989), close=3075)
    assert_data(strat.data, 0, datetime.datetime(2015, 9, 26, 23, 59, 59, 999989), close=3078)


def test_tcal_8_to_20():
    """Read tick data and resample to 1 day bars according to trading calendar."""
    strat = _run_cerebro(use_tcal=True,
                        open_hour=8,
                        open_minute=0,
                        close_hour=20,
                        close_minute=0,
                        )

    assert len(strat) == 3

    assert_data(strat.data, -2, datetime.datetime(2015, 9, 24, 20, 0, 0), close=3500)
    assert_data(strat.data, -1, datetime.datetime(2015, 9, 25, 20, 0, 0), close=3074)
    assert_data(strat.data, 0, datetime.datetime(2015, 9, 26, 20, 0, 0), close=3078)


def test_tcal_8_to_20_30(main=False):
    """Trading calenadar times are a bit longer and contain some more ticks that would be filtered otherwise."""
    strat = _run_cerebro(use_tcal=True,
                        open_hour=8,
                        open_minute=0,
                        close_hour=20,
                        close_minute=30,
                        )

    assert len(strat) == 3

    assert_data(strat.data, -2, datetime.datetime(2015, 9, 24, 20, 30, 0), close=3600)
    assert_data(strat.data, -1, datetime.datetime(2015, 9, 25, 20, 30, 0), close=3074)
    assert_data(strat.data, 0, datetime.datetime(2015, 9, 26, 20, 30, 0), close=3078)


@pytest.mark.timeout(5)
def test_bug_tcal_infinite_loop():
    """# results in an endless loop with standard bt because 22:00:02 is always outside of trading hours
    # should be fixed in my branch!?"""
    tradingcal = bt.TradingCalendar(open=datetime.time(hour=12), close=datetime.time(hour=22))

    tradingcal.schedule(datetime.datetime(2018, 1, 1, 22, 0, 2))


def test_bug_tcal_nodaycheck():
    tradingcal = bt.TradingCalendar(open=datetime.time(hour=12),
                                    close=datetime.time(hour=22),
                                    earlydays=[(datetime.date(2018, 11, 23), datetime.time(hour=12), datetime.time(hour=20))])

    sched = tradingcal.schedule(datetime.datetime(2018, 11, 23, 20, 10, 0))

    # should skip saturday and sunday and return monday (26-11-2018)
    assert(sched == (datetime.datetime(2018, 11, 26, 12), datetime.datetime(2018, 11, 26, 22)))


def test_bug_tcal_utc_overflow():
    """the requested timestamp actually is date '2018-11-20' (not 21th) according to exhchange's timezone 'Pacific/Auckland' so it should return trading hours
    for that date. those trading hours differ since they are defined by the earlydays parameter (instead of regular trading hours)"""
    tradingcal = bt.TradingCalendar(open=datetime.time(hour=10),
                                    close=datetime.time(hour=16, minute=45),
                                    earlydays=[(datetime.date(2018, 11, 20), datetime.time(hour=9), datetime.time(hour=18))],
                                    )

    sched = tradingcal.schedule(datetime.datetime(2018, 11, 21, 3, 0, 0), pytz.timezone('Pacific/Auckland'))

    assert (sched == (datetime.datetime(2018, 11, 20, 21), datetime.datetime(2018, 11, 21, 3, 45)))
