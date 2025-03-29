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
"""
BOLLINGER BANDS RSI WITH ATR STRATEGY - (bb_rsi_atr)
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
python strategies/bb_rsi_atr.py --data SPY --fromdate 2024-01-01 --todate 2024-12-31 --plot
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import os
import sys
import backtrader as bt
import backtrader.indicators as btind

# Import utility functions
try:
    from strategies.utils import get_db_data, print_performance_metrics, TradeThrottling, add_standard_analyzers
except ModuleNotFoundError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from strategies.utils import get_db_data, print_performance_metrics, TradeThrottling, add_standard_analyzers

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class StockPriceData(bt.feeds.PandasData):
    """Stock Price Data Feed"""
    params = (
        ('datetime', None),
        ('open', 'Open'),
        ('high', 'High'),
        ('low', 'Low'),
        ('close', 'Close'),
        ('volume', 'Volume'),
    )


class BBRSIATRStrategy(bt.Strategy, TradeThrottling):
    """Bollinger Bands RSI with ATR Strategy"""
    params = (
        ('bb_length', 20),
        ('bb_mult', 2.0),
        ('bb_matype', 'SMA'),
        ('bb_src', 'close'),
        ('rsi_length', 11),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('stop_loss_pct', 50.0),  # Effectively disabled to match PineScript
        ('trailing_stop_pct', 50.0),  # Effectively disabled to match PineScript
        ('atr_length', 14),
        ('atr_mult', 5.0),  # Increased to reduce trade frequency
        ('start_year', 2024),
        ('start_month', 1),
        ('start_day', 1),
        ('end_year', 2024),
        ('end_month', 12),
        ('end_day', 31),
        ('loglevel', 'info'),
    )

    def log(self, txt, dt=None, level='info'):
        if level == 'debug' and self.p.loglevel != 'debug':
            return
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        src_map = {'open': self.datas[0].open, 'high': self.datahigh, 
                  'low': self.datalow, 'close': self.dataclose}
        self.datasrc = src_map.get(self.p.bb_src, self.dataclose)

        # Indicators
        ma_types = {
            'SMA': btind.SimpleMovingAverage,
            'EMA': btind.ExponentialMovingAverage,
            'SMMA (RMA)': btind.SmoothedMovingAverage,
            'WMA': btind.WeightedMovingAverage,
            'VWMA': btind.MovingAverageSimple  # Fallback
        }
        ma_class = ma_types.get(self.p.bb_matype, btind.SimpleMovingAverage)
        
        self.bbands = btind.BollingerBands(self.datasrc, period=self.p.bb_length, 
                                          devfactor=self.p.bb_mult, movav=ma_class)
        self.rsi = btind.RSI(self.datasrc, period=self.p.rsi_length)
        self.atr = btind.ATR(self.datas[0], period=self.p.atr_length)
        self.atr_avg = btind.SimpleMovingAverage(self.atr, period=self.p.atr_length)
        
        self.order = None
        self.entry_price = None
        self.stop_price = None
        self.trailing_price = None
        self.total_commission = 0.0
        self.last_trade_date = None
        self.entry_bar = None  # Track entry bar for trade duration
        self.trade_durations = []  # Store trade durations

        self.start_date = datetime.datetime(self.p.start_year, self.p.start_month, self.p.start_day)
        self.end_date = datetime.datetime(self.p.end_year, self.p.end_month, self.p.end_day)

    def is_in_date_range(self):
        current_date = self.datas[0].datetime.datetime(0)
        return self.start_date <= current_date <= self.end_date

    def volatility_filter(self):
        return self.atr[0] < self.atr_avg[0] * self.p.atr_mult

    def calculate_position_size(self):
        cash = self.broker.getcash()
        price = self.dataclose[0]
        return max(1, cash / price) if price > 0 else 0

    def next(self):
        if not self.is_in_date_range() or self.order:
            return

        # Exit logic
        if self.position:
            # Check stop loss and trailing stop against close only
            active_stop = max(self.stop_price or -float('inf'), self.trailing_price or -float('inf'))
            if self.dataclose[0] <= active_stop:
                self.log(f'STOP TRIGGERED: Close {self.dataclose[0]:.2f}, Stop {active_stop:.2f}')
                self.order = self.close(exectype=bt.Order.Close)
                return
            
            # Profit-taking exit
            if self.datasrc[0] >= self.bbands.top[0] and self.rsi[0] > self.p.rsi_overbought:
                self.log(f'PROFIT EXIT: Close {self.datasrc[0]:.2f}, Upper BB {self.bbands.top[0]:.2f}, RSI {self.rsi[0]:.2f}')
                self.order = self.close(exectype=bt.Order.Close)
                return
            
            # Update trailing stop
            trail_offset = self.entry_price * (self.p.trailing_stop_pct / 100)
            potential_trail = self.dataclose[0] - trail_offset
            if not self.trailing_price or potential_trail > self.trailing_price:
                self.trailing_price = potential_trail
                self.log(f'TRAILING STOP UPDATED: {self.trailing_price:.2f}', level='debug')

        # Entry logic
        elif (self.datasrc[0] <= self.bbands.bot[0] and 
              self.rsi[0] < self.p.rsi_oversold and 
              self.volatility_filter()):
            size = self.calculate_position_size()
            self.order = self.buy(size=size, exectype=bt.Order.Close)
            self.log(f'BUY CREATE: Close {self.dataclose[0]:.2f}, Size {size:.2f}')
            self.entry_bar = self.data.datetime[0]  # Record entry bar

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status == order.Completed:
            self.total_commission += order.executed.comm
            if order.isbuy():
                self.entry_price = self.dataclose[0]  # Use close price for consistency
                self.stop_price = self.entry_price * (1 - self.p.stop_loss_pct / 100)
                self.trailing_price = None
                self.last_trade_date = self.datas[0].datetime.date(0)
                self.log(f'BUY EXECUTED: Price {order.executed.price:.2f}, Size {order.executed.size:.2f}, '
                         f'Stop {self.stop_price:.2f}, Comm {order.executed.comm:.2f}')
            else:
                profit = (order.executed.price - self.entry_price) * order.executed.size if self.entry_price else 0
                # Calculate trade duration
                if self.entry_bar:
                    exit_bar = self.data.datetime[0]
                    duration = (exit_bar - self.entry_bar).total_seconds() / 3600  # Convert to hours (1h timeframe)
                    self.trade_durations.append(duration)
                    self.log(f'TRADE DURATION: {duration:.0f} bars (hours)')
                self.log(f'SELL EXECUTED: Price {order.executed.price:.2f}, Size {order.executed.size:.2f}, '
                         f'Profit {profit:.2f}, Comm {order.executed.comm:.2f}')
                self.entry_price = None
                self.stop_price = None
                self.trailing_price = None
                self.entry_bar = None
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Failed: {order.status}')
        
        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f'TRADE CLOSED: Gross PnL {trade.pnl:.2f}, Net PnL {trade.pnlcomm:.2f}')

    def stop(self):
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}')
        if self.trade_durations:
            avg_duration = sum(self.trade_durations) / len(self.trade_durations)
            self.log(f'Average Trade Duration: {avg_duration:.0f} bars (hours)')


def parse_args():
    parser = argparse.ArgumentParser(description='Bollinger Bands RSI with ATR Strategy',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--data', '-d', required=True, help='Stock symbol')
    parser.add_argument('--dbuser', '-u', default='jason', help='PostgreSQL username')
    parser.add_argument('--dbpass', '-pw', default='fsck', help='PostgreSQL password')
    parser.add_argument('--dbname', '-n', default='market_data', help='PostgreSQL database name')
    parser.add_argument('--fromdate', '-f', default='2024-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--todate', '-t', default='2024-12-31', help='End date (YYYY-MM-DD)')
    parser.add_argument('--cash', '-c', default=1000000.0, type=float, help='Starting cash')  # Match PineScript
    parser.add_argument('--commission', '-cm', default=0.0, type=float, help='Commission percentage')
    parser.add_argument('--interval', '-i', default='1h', choices=['1h', '4h', '1d'], help='Data interval')
    parser.add_argument('--bb-length', '-bl', default=20, type=int, help='Bollinger Bands period')
    parser.add_argument('--bb-mult', '-bm', default=2.0, type=float, help='BB std dev multiplier')
    parser.add_argument('--matype', '-mt', default='SMA', choices=['SMA', 'EMA', 'SMMA (RMA)', 'WMA', 'VWMA'], 
                        help='Moving average type')
    parser.add_argument('--src', '-s', default='close', choices=['open', 'high', 'low', 'close'], help='Price source')
    parser.add_argument('--rsi-length', '-rl', default=11, type=int, help='RSI period')
    parser.add_argument('--rsi-oversold', '-ro', default=30, type=int, help='RSI oversold threshold')
    parser.add_argument('--rsi-overbought', '-rb', default=70, type=int, help='RSI overbought threshold')
    parser.add_argument('--stop-loss', '-sl', default=50.0, type=float, help='Stop loss percentage')
    parser.add_argument('--trailing-stop', '-ts', default=50.0, type=float, help='Trailing stop percentage')
    parser.add_argument('--atr-length', '-al', default=14, type=int, help='ATR period')
    parser.add_argument('--atr-mult', '-am', default=5.0, type=float, help='ATR volatility multiplier')
    parser.add_argument('--start-year', '-sy', default=2024, type=int, help='Start year')
    parser.add_argument('--start-month', '-sm', default=1, type=int, help='Start month')
    parser.add_argument('--start-day', '-sd', default=1, type=int, help='Start day')
    parser.add_argument('--end-year', '-ey', default=2024, type=int, help='End year')
    parser.add_argument('--end-month', '-em', default=12, type=int, help='End month')
    parser.add_argument('--end-day', '-ed', default=31, type=int, help='End day')
    parser.add_argument('--plot', '-pl', action='store_true', help='Plot trading activity')
    return parser.parse_args()


def main():
    args = parse_args()
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
    padded_fromdate = datetime.datetime(fromdate.year, 1, 1)

    df = get_db_data(args.data, args.dbuser, args.dbpass, args.dbname, padded_fromdate, todate, args.interval)
    data = StockPriceData(dataname=df, fromdate=fromdate, todate=todate)

    cerebro = bt.Cerebro(cheat_on_close=True)
    cerebro.adddata(data)
    cerebro.addstrategy(
        BBRSIATRStrategy,
        bb_length=args.bb_length, bb_mult=args.bb_mult, bb_matype=args.matype, bb_src=args.src,
        rsi_length=args.rsi_length, rsi_oversold=args.rsi_oversold, rsi_overbought=args.rsi_overbought,
        stop_loss_pct=args.stop_loss, trailing_stop_pct=args.trailing_stop,
        atr_length=args.atr_length, atr_mult=args.atr_mult,
        start_year=args.start_year, start_month=args.start_month, start_day=args.start_day,
        end_year=args.end_year, end_month=args.end_month, end_day=args.end_day
    )
    cerebro.broker.setcash(args.cash)
    cerebro.broker.setcommission(commission=args.commission / 100)
    cerebro.broker.set_slippage_perc(0.0)
    add_standard_analyzers(cerebro)

    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')
    results = cerebro.run()
    print(f'Final Portfolio Value: ${cerebro.broker.getvalue():.2f}')
    print_performance_metrics(cerebro, results, fromdate, todate)

    if args.plot:
        cerebro.plot(style='candlestick', barup='green', bardown='red')


if __name__ == '__main__':
    main()