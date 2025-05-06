#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2023-2025
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
"""BOLLINGER BANDS RSI WITH ATR STRATEGY - (bb_rsi_atr)
===================================================
Translated from PineScript to Backtrader. Buys when price closes at/below lower
Bollinger Band, RSI < 30, and ATR < ATR_avg * 5.0; exits when price closes at/above
upper Bollinger Band and RSI > 70.
STRATEGY LOGIC:
--------------
- LONG Entry: Price <= Lower BB, RSI < 30, ATR < ATR_avg * 5.0
- LONG Exit: Price >= Upper BB and RSI > 70
- Position: 100% of equity
MARKET CONDITIONS:
-----------------
Designed for range-bound markets. Avoid strong trends.
USAGE:
------
python strategies/bb_rsi_atr.py --data SPY --fromdate 2024-01-01 --todate 2024-12-31 --plot"""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import argparse
import datetime
import os
import sys

import backtrader as bt
import backtrader.indicators as btind

# Import utility functions
try:
    from strategies.utils import (
        TradeThrottling,
        add_standard_analyzers,
        get_db_data,
        print_performance_metrics,
    )
except ModuleNotFoundError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from strategies.utils import (
        TradeThrottling,
        add_standard_analyzers,
        get_db_data,
        print_performance_metrics,
    )

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class StockPriceData(bt.feeds.PandasData):
    """Stock Price Data Feed"""

    params = (
        ("datetime", None),
        ("open", "Open"),
        ("high", "High"),
        ("low", "Low"),
        ("close", "Close"),
        ("volume", "Volume"),
    )


class BBRSIATRStrategy(bt.Strategy, TradeThrottling):
    """Bollinger Bands RSI with ATR Strategy"""

    params = (
        ("bb_length", 20),
        ("bb_mult", 2.0),
        ("bb_matype", "SMA"),
        ("bb_src", "close"),
        ("rsi_length", 11),
        ("rsi_oversold", 30),
        ("rsi_overbought", 70),
        ("stop_loss_pct", 50.0),  # Effectively disabled to match PineScript
        ("trailing_stop_pct", 50.0),  # Effectively disabled to match PineScript
        ("atr_length", 14),
        ("atr_mult", 5.0),  # Increased to reduce trade frequency
        ("start_year", 2024),
        ("start_month", 1),
        ("start_day", 1),
        ("end_year", 2024),
        ("end_month", 12),
        ("end_day", 31),
        ("loglevel", "info"),
    )

    def log(self, txt, dt=None, level="info"):
"""Args::
    txt: 
    dt: (Default value = None)
    level: (Default value = "info")"""
    level: (Default value = "info")"""
        if level == "debug" and self.p.loglevel != "debug":
            return
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}: {txt}")

    def __init__(self):
""""""
""""""
""""""
""""""
""""""
"""Args::
    order:"""
"""Args::
    trade:"""
""""""
""""""
""""""
    args = parse_args()
    fromdate = datetime.datetime.strptime(args.fromdate, "%Y-%m-%d")
    todate = datetime.datetime.strptime(args.todate, "%Y-%m-%d")
    padded_fromdate = datetime.datetime(fromdate.year, 1, 1)

    df = get_db_data(
        args.data,
        args.dbuser,
        args.dbpass,
        args.dbname,
        padded_fromdate,
        todate,
        args.interval,
    )
    data = StockPriceData(dataname=df, fromdate=fromdate, todate=todate)

    cerebro = bt.Cerebro(cheat_on_close=True)
    cerebro.adddata(data)
    cerebro.addstrategy(
        BBRSIATRStrategy,
        bb_length=args.bb_length,
        bb_mult=args.bb_mult,
        bb_matype=args.matype,
        bb_src=args.src,
        rsi_length=args.rsi_length,
        rsi_oversold=args.rsi_oversold,
        rsi_overbought=args.rsi_overbought,
        stop_loss_pct=args.stop_loss,
        trailing_stop_pct=args.trailing_stop,
        atr_length=args.atr_length,
        atr_mult=args.atr_mult,
        start_year=args.start_year,
        start_month=args.start_month,
        start_day=args.start_day,
        end_year=args.end_year,
        end_month=args.end_month,
        end_day=args.end_day,
    )
    cerebro.broker.setcash(args.cash)
    cerebro.broker.setcommission(commission=args.commission / 100)
    cerebro.broker.set_slippage_perc(0.0)
    add_standard_analyzers(cerebro)

    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")
    results = cerebro.run()
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():.2f}")
    print_performance_metrics(cerebro, results, fromdate, todate)

    if args.plot:
        cerebro.plot(style="candlestick", barup="green", bardown="red")


if __name__ == "__main__":
    main()
