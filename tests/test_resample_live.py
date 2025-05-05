#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime

import backtrader as bt
import logging
from freezegun import freeze_time
from util_asserts import assert_data

_logger = logging.getLogger(__name__)


def _get_trading_calendar(open_hour, close_hour, close_minute):
    cal = bt.TradingCalendar(open=datetime.time(hour=open_hour), close=datetime.time(hour=close_hour, minute=close_minute))
    return cal


def _run_resampler(data_timeframe,
                   data_compression,
                   resample_timeframe,
                   resample_compression,
                   num_gen_bars,
                   runtime_seconds=27,
                   starting_value=200,
                   tick_interval=datetime.timedelta(seconds=25),
                   live=False,
                   ) -> bt.Strategy:
    _logger.info("Constructing Cerebro")
    cerebro = bt.Cerebro(bar_on_exit=False)
    cerebro.addstrategy(bt.strategies.NullStrategy)

    data = bt.feeds.FakeFeed(timeframe=data_timeframe,
                             compression=data_compression,
                             run_duration=datetime.timedelta(seconds=runtime_seconds),
                             starting_value=starting_value,
                             tick_interval=tick_interval,
                             live=live,
                             num_gen_bars=num_gen_bars,
                             )

    cerebro.resampledata(data, timeframe=resample_timeframe, compression=resample_compression)

    # return the recorded bars attribute from the first strategy
    return cerebro.run()[0]


@freeze_time("Jan 1th, 2000", tick=True)
def test_live_m1_to_m5_rt():
    strat = _run_resampler(live=True,
                           data_timeframe=bt.TimeFrame.Minutes,
                           data_compression=1,
                           resample_timeframe=bt.TimeFrame.Minutes,
                           resample_compression=5,
                           num_gen_bars=0,
                           runtime_seconds=310,
                           )

    assert(len(strat) == 1)

    assert_data(strat.data, -1, datetime.datetime(2000, 1, 1, 0, 5), open=200, close=204)


@freeze_time("Jan 1th, 2000", tick=True)
def test_live_ticks_to_m1_rt():
    strat = _run_resampler(live=True,
                           data_timeframe=bt.TimeFrame.Ticks,
                           data_compression=1,
                           resample_timeframe=bt.TimeFrame.Minutes,
                           resample_compression=1,
                           runtime_seconds=130,
                           num_gen_bars=0,
                           tick_interval=datetime.timedelta(seconds=27),
                           )

    assert(len(strat) == 2)

    assert_data(strat.data, -1, datetime.datetime(2000, 1, 1, 0, 1, 0), open=200, close=201)
    assert_data(strat.data, 0, datetime.datetime(2000, 1, 1, 0, 2, 0), open=202, close=203)


@freeze_time("Jan 1th, 2000", tick=True)
def test_live_m1_to_m3_rt():
    strat = _run_resampler(live=True,
                           data_timeframe=bt.TimeFrame.Minutes,
                           data_compression=1,
                           tick_interval=datetime.timedelta(seconds=25),
                           resample_timeframe=bt.TimeFrame.Minutes,
                           resample_compression=3,
                           num_gen_bars=0,
                           runtime_seconds=190,
                           )

    assert (len(strat) == 1)

    assert_data(strat.data, 0, datetime.datetime(2000, 1, 1, 0, 3, 0), open=200, close=202)


@freeze_time("Jan 1th, 2000 23:58", tick=True)
def test_live_ticks_to_m3_eos_rt():
    strat = _run_resampler(live=True,
                           data_timeframe=bt.TimeFrame.Ticks,
                           data_compression=1,
                           tick_interval=datetime.timedelta(seconds=25),
                           resample_timeframe=bt.TimeFrame.Minutes,
                           resample_compression=3,
                           num_gen_bars=0,
                           runtime_seconds=190,
                           )

    assert (len(strat) == 1)

    assert_data(strat.data, -1, datetime.datetime(2000, 1, 1, 23, 59, 59, 999989), open=200, close=203)


@freeze_time("Jan 1th, 2000", tick=True)
def test_live_m1_to_m3_ff():
    strat = _run_resampler(live=False,
                           num_gen_bars=10,
                           data_timeframe=bt.TimeFrame.Minutes,
                           data_compression=1,
                           resample_timeframe=bt.TimeFrame.Minutes,
                           resample_compression=3,
                           )
    assert (len(strat) == 3)

    assert_data(strat.data, -1, datetime.datetime(2000, 1, 1, 0, 9, 0), open=206, close=208)
    assert_data(strat.data, -2, datetime.datetime(2000, 1, 1, 0, 6, 0), open=203, close=205)
    assert_data(strat.data, -3, datetime.datetime(2000, 1, 1, 0, 3, 0), open=200, close=202)


@freeze_time("Jan 1th, 2000", tick=True)
def test_live_d1_to_d3_ff():
    """This is testing the componly path in Resampler."""
    strat = _run_resampler(live=False,
                           num_gen_bars=10,
                           data_timeframe=bt.TimeFrame.Days,
                           data_compression=1,
                           resample_timeframe=bt.TimeFrame.Days,
                           resample_compression=3,
                           )

    assert (len(strat) == 3)

    assert_data(strat.data, -1, datetime.datetime(2000, 1, 10, 23, 59, 59, 999989), open=206, close=208)
    assert_data(strat.data, -2, datetime.datetime(2000, 1, 7, 23, 59, 59, 999989), open=203, close=205)
    assert_data(strat.data, -3, datetime.datetime(2000, 1, 4, 23, 59, 59, 999989), open=200, close=202)


@freeze_time("Jan 1th, 2000 23:59:00", tick=True)
def test_live_ticks_to_d1_rt():
    strat = _run_resampler(live=True,
                           data_timeframe=bt.TimeFrame.Ticks,
                           data_compression=1,
                           resample_timeframe=bt.TimeFrame.Days,
                           resample_compression=1,
                           runtime_seconds=80,
                           num_gen_bars=0,
                           tick_interval=datetime.timedelta(seconds=7),
                           )

    assert (len(strat) == 1)

    assert_data(strat.data, -1, datetime.datetime(2000, 1, 1, 23, 59, 59, 999989), open=200, close=207)


@freeze_time("Jan 1th, 2000 09:30:00", tick=True)
def test_live_ticks_to_h1_ff():
    strat = _run_resampler(live=False,
                           data_timeframe=bt.TimeFrame.Ticks,
                           data_compression=1,
                           resample_timeframe=bt.TimeFrame.Minutes,
                           resample_compression=60,
                           tick_interval=datetime.timedelta(seconds=230),
                           num_gen_bars=38,
                           )
    assert (len(strat) == 2)

    assert_data(strat.data, -1, datetime.datetime(2000, 1, 1, 11, 0, 0), open=207, close=222)
    assert_data(strat.data, -2, datetime.datetime(2000, 1, 1, 10, 0, 0), open=200, close=206)
