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
RSI DIVERGENCE TRADING STRATEGY - (rsi-divergence)
==================================================

This strategy identifies and trades on RSI divergences:
- Bullish divergence: Price makes a lower low while RSI makes a higher low (oversold)
- Bearish divergence: Price makes a higher high while RSI makes a lower high (overbought)

STRATEGY LOGIC:
--------------
- Identify RSI divergences by comparing price lows/highs with RSI lows/highs
- Enter long on bullish divergence when price is in an uptrend or crosses above SMA
- Enter short on bearish divergence when price is in a downtrend or crosses below SMA
- Apply position sizing based on risk management (ATR-based stops)
- Use multiple exit mechanisms including trailing stops and RSI thresholds

MARKET CONDITIONS:
----------------
*** THIS STRATEGY PERFORMS BEST IN TRENDING MARKETS WITH PULLBACKS ***
It looks for price corrections against the main trend that aren't confirmed
by momentum (RSI), signaling potential trend resumption.

EXAMPLE COMMANDS:
---------------
1. Standard configuration - default RSI divergence detection:
   python strategies/rsi_divergence.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31

2. More sensitive RSI settings - faster divergence signals:
   python strategies/rsi_divergence.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --rsi-period 10 --divergence-lookback 15

3. Extreme overbought/oversold thresholds - fewer but stronger signals:
   python strategies/rsi_divergence.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --rsi-oversold 25 --rsi-overbought 75 --exit-rsi-thresh 40 --exit-rsi-thresh-short 60

4. Trend-filtered approach - stronger trend confirmation:
   python strategies/rsi_divergence.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --trend-sma-period 100

5. Aggressive risk/reward profile - larger position sizing with wider stops:
   python strategies/rsi_divergence.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --risk-percent 2.0 --stop-atr-multiple 2.5 --tp-sl-ratio 3.0

USAGE:
------
python strategies/rsi_divergence.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2018-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2023-12-31)

DATABASE PARAMETERS:
------------------
--dbuser, -u    : PostgreSQL username (default: jason)
--dbpass, -pw   : PostgreSQL password (default: fsck)
--dbname, -n    : PostgreSQL database name (default: market_data)
--cash, -c      : Initial cash for the strategy (default: $100,000)

RSI AND DIVERGENCE PARAMETERS:
----------------------------
--rsi-period, -rp        : RSI calculation period (default: 14)
--divergence-lookback, -dl : Periods to look back for divergence (default: 20)
--rsi-oversold, -ro      : RSI oversold level (default: 30)
--rsi-overbought, -rob   : RSI overbought level (default: 70)

TREND CONFIRMATION:
-----------------
--trend-sma, -ts         : SMA period for trend confirmation (default: 50)

EXIT PARAMETERS:
--------------
--exit-rsi-thresh, -ert   : RSI threshold to exit longs (default: 45)
--exit-rsi-thresh-short, -erts : RSI threshold to exit shorts (default: 55)

RISK MANAGEMENT:
--------------
--risk-percent, -rip      : Risk per trade as percentage of portfolio (default: 1.0)
--stop-atr-multiple, -sam : ATR multiplier for stop loss (default: 2.0) 
--atr-period, -ap         : ATR period (default: 14)
--tp-sl-ratio, -tsr       : Take profit to stop loss ratio (default: 2.0)

TRADE THROTTLING:
---------------
--trade-throttle-days, -ttd : Minimum days between trades (default: 5)

OTHER:
-----
--plot, -p      : Generate and show a plot of the trading activity

EXAMPLE:
--------
python strategies/rsi_divergence.py --data AAPL --fromdate 2023-01-01 --todate 2023-12-31 --rsi-period 14 --plot
"""

import argparse
import datetime
import os
import sys
import numpy as np
import pandas as pd
import backtrader as bt

# Add the parent directory to the Python path to import shared modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utility functions
from strategies.utils import (get_db_data, print_performance_metrics, 
                            TradeThrottling, add_standard_analyzers)


class StockPriceData(bt.feeds.PandasData):
    """
    Stock Price Data Feed
    """
    params = (
        ('datetime', None),  # Column containing the date (index)
        ('open', 'Open'),    # Column containing the open price
        ('high', 'High'),    # Column containing the high price
        ('low', 'Low'),      # Column containing the low price
        ('close', 'Close'),  # Column containing the close price
        ('volume', 'Volume'), # Column containing the volume
        ('openinterest', None)  # Column for open interest (not available)
    )


class RSIDivergenceStrategy(bt.Strategy, TradeThrottling):
    """
    RSI Divergence Strategy for Backtrader
    
    This strategy identifies and trades on RSI divergences:
    - Bullish divergence: Price makes a lower low while RSI makes a higher low (oversold)
    - Bearish divergence: Price makes a higher high while RSI makes a lower high (overbought)
    
    Additional filters include RSI overbought/oversold levels and moving average trend confirmation.
    """
    
    params = (
        ('rsi_period', 14),         # RSI lookback period
        ('divergence_lookback', 20), # Periods to look back for divergence
        ('trend_sma_period', 50),   # SMA period for trend direction
        ('rsi_oversold', 30),       # RSI oversold threshold
        ('rsi_overbought', 70),     # RSI overbought threshold
        ('risk_percent', 1.0),      # Risk per trade as percentage of portfolio
        ('stop_atr_multiple', 2.0), # ATR multiplier for stop loss
        ('atr_period', 14),         # ATR period
        ('tp_sl_ratio', 2.0),       # Take profit to stop loss ratio
        ('exit_rsi_thresh', 45),    # Exit long when RSI goes above this
        ('exit_rsi_thresh_short', 55),  # Exit short when RSI falls below this
        ('trade_throttle_days', 5), # Minimum days between trades
        ('log_level', 'info'),      # Logging level (debug, info, warning, error)
    )
    
    def __init__(self):
        """Initialize the strategy"""
        # Calculate indicators
        # RSI indicator
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        
        # Trend confirmation SMA
        self.sma = bt.indicators.SMA(self.data.close, period=self.p.trend_sma_period)
        
        # ATR for stop loss and volatility measurement
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        # For storing swing highs/lows
        self.price_highs = []
        self.price_lows = []
        self.rsi_highs = []
        self.rsi_lows = []
        
        # Divergence detection flags
        self.divergence_bull = False
        self.divergence_bear = False
        
        # For tracking orders and positions
        self.buy_order = None
        self.sell_order = None
        self.stop_loss = None
        self.take_profit = None
        self.order_price = None
        self.position_size = 0
        
        # For trade throttling
        self.last_trade_date = None
        
        # For plotting - removed plot parameter to avoid TypeError
        self.bull_divergence_signal = bt.indicators.Max(0)
        self.bear_divergence_signal = bt.indicators.Max(0)
    
    def log(self, txt, dt=None, level='info'):
        """Logging function for this strategy"""
        if level == 'debug' and self.p.log_level != 'debug':
            return
            
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')
    
    def notify_order(self, order):
        """Called when an order is placed, filled, or canceled."""
        # Skip if order is not completed
        if order.status in [order.Submitted, order.Accepted]:
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Size: {order.executed.size}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.order_price = order.executed.price
                self.position_size = order.executed.size
                # Set stop loss and take profit on buy
                self.set_exit_orders(order.executed.price, is_buy=True)
                # Update last trade date for throttling
                self.last_trade_date = self.datas[0].datetime.date(0)
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Size: {order.executed.size}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.order_price = order.executed.price
                self.position_size = order.executed.size
                # Set stop loss and take profit on sell
                self.set_exit_orders(order.executed.price, is_buy=False)
                # Update last trade date for throttling
                self.last_trade_date = self.datas[0].datetime.date(0)
        
        # Handle failed or canceled orders
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected: {order.status}')
        
        # Reset order references
        if order == self.buy_order:
            self.buy_order = None
        elif order == self.sell_order:
            self.sell_order = None
        elif order == self.stop_loss:
            self.stop_loss = None
        elif order == self.take_profit:
            self.take_profit = None
    
    def notify_trade(self, trade):
        """Called when a trade is completed."""
        if not trade.isclosed:
            return
        
        self.log(f'TRADE COMPLETED: PnL: Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')
    
    def set_exit_orders(self, entry_price, is_buy=True):
        """Set stop loss and take profit orders"""
        # Cancel existing exit orders
        self.cancel_exit_orders()
        
        atr_val = self.atr[0]
        
        if is_buy:
            # Set stop loss for long positions
            stop_price = entry_price - (atr_val * self.p.stop_atr_multiple)
            profit_target = entry_price + ((entry_price - stop_price) * self.p.tp_sl_ratio)
            
            self.stop_loss = self.sell(exectype=bt.Order.Stop, price=stop_price, size=self.position_size)
            self.take_profit = self.sell(exectype=bt.Order.Limit, price=profit_target, size=self.position_size)
            
            self.log(f'Long position: Entry at {entry_price:.2f}, Stop at {stop_price:.2f}, Target at {profit_target:.2f}')
        else:
            # Set stop loss for short positions
            stop_price = entry_price + (atr_val * self.p.stop_atr_multiple)
            profit_target = entry_price - ((stop_price - entry_price) * self.p.tp_sl_ratio)
            
            self.stop_loss = self.buy(exectype=bt.Order.Stop, price=stop_price, size=self.position_size)
            self.take_profit = self.buy(exectype=bt.Order.Limit, price=profit_target, size=self.position_size)
            
            self.log(f'Short position: Entry at {entry_price:.2f}, Stop at {stop_price:.2f}, Target at {profit_target:.2f}')
    
    def cancel_exit_orders(self):
        """Cancel stop loss and take profit orders"""
        if self.stop_loss is not None:
            self.cancel(self.stop_loss)
            self.stop_loss = None
        
        if self.take_profit is not None:
            self.cancel(self.take_profit)
            self.take_profit = None
    
    def calculate_position_size(self, stop_price):
        """Calculate position size based on risk percentage"""
        risk_amount = self.broker.getvalue() * (self.p.risk_percent / 100)
        price = self.data.close[0]
        risk_per_share = abs(price - stop_price)
        
        if risk_per_share > 0:
            size = risk_amount / risk_per_share
            return int(size)
        return 1  # Default to 1 if calculation fails
    
    def get_safe_price_value(self, idx=0):
        """Safely get price values without risk of index errors"""
        try:
            return self.data.close[idx]
        except IndexError:
            return None
            
    def get_safe_rsi_value(self, idx=0):
        """Safely get RSI values without risk of index errors"""
        try:
            return self.rsi[idx]
        except IndexError:
            return None
    
    def is_local_price_minimum(self):
        """Check if the previous bar formed a local price minimum"""
        # Need at least 3 bars
        if len(self.data) < 3:
            return False
            
        # Get values safely
        current = self.get_safe_price_value(0)
        prev = self.get_safe_price_value(1)
        prev2 = self.get_safe_price_value(2)
        
        if None in (current, prev, prev2):
            return False
            
        # Check for local minimum at previous bar
        return prev2 > prev and prev < current
    
    def is_local_price_maximum(self):
        """Check if the previous bar formed a local price maximum"""
        # Need at least 3 bars
        if len(self.data) < 3:
            return False
            
        # Get values safely
        current = self.get_safe_price_value(0)
        prev = self.get_safe_price_value(1)
        prev2 = self.get_safe_price_value(2)
        
        if None in (current, prev, prev2):
            return False
            
        # Check for local maximum at previous bar
        return prev2 < prev and prev > current
    
    def is_local_rsi_minimum(self):
        """Check if the previous bar formed a local RSI minimum"""
        # Need at least 3 bars
        if len(self.data) < 3:
            return False
            
        # Get values safely
        current = self.get_safe_rsi_value(0)
        prev = self.get_safe_rsi_value(1)
        prev2 = self.get_safe_rsi_value(2)
        
        if None in (current, prev, prev2):
            return False
            
        # Check for local minimum at previous bar
        return prev2 > prev and prev < current
    
    def is_local_rsi_maximum(self):
        """Check if the previous bar formed a local RSI maximum"""
        # Need at least 3 bars
        if len(self.data) < 3:
            return False
            
        # Get values safely
        current = self.get_safe_rsi_value(0)
        prev = self.get_safe_rsi_value(1)
        prev2 = self.get_safe_rsi_value(2)
        
        if None in (current, prev, prev2):
            return False
            
        # Check for local maximum at previous bar
        return prev2 < prev and prev > current
    
    def find_divergences(self):
        """Detect RSI divergences - safely handles array indices"""
        # Reset divergence flags
        self.divergence_bull = False
        self.divergence_bear = False
        
        # Make sure we have enough bars for analysis
        # Need at least RSI period + a few bars to identify patterns
        min_bars_needed = self.p.rsi_period + 5
        if len(self) <= min_bars_needed:
            return
            
        # Current values - always safe to access index 0
        current_close = self.data.close[0]
        current_rsi = self.rsi[0]
        
        # Previous bar's values - check for local extremes safely using our helper methods
        if self.is_local_price_minimum():
            # Get the previous bar's close
            prev_close = self.get_safe_price_value(1)
            # We have a local price minimum at previous bar
            self.price_lows.append((len(self)-1, prev_close))
            # Keep only recent lows within lookback period
            self.price_lows = [x for x in self.price_lows if x[0] > len(self) - self.p.divergence_lookback]
        
        if self.is_local_price_maximum():
            # Get the previous bar's close
            prev_close = self.get_safe_price_value(1)
            # We have a local price maximum at previous bar
            self.price_highs.append((len(self)-1, prev_close))
            # Keep only recent highs within lookback period
            self.price_highs = [x for x in self.price_highs if x[0] > len(self) - self.p.divergence_lookback]
        
        # Same for RSI
        if self.is_local_rsi_minimum():
            # Get the previous bar's RSI
            prev_rsi = self.get_safe_rsi_value(1)
            # We have a local RSI minimum at previous bar
            self.rsi_lows.append((len(self)-1, prev_rsi))
            # Keep only recent lows within lookback period
            self.rsi_lows = [x for x in self.rsi_lows if x[0] > len(self) - self.p.divergence_lookback]
        
        if self.is_local_rsi_maximum():
            # Get the previous bar's RSI
            prev_rsi = self.get_safe_rsi_value(1)
            # We have a local RSI maximum at previous bar
            self.rsi_highs.append((len(self)-1, prev_rsi))
            # Keep only recent highs within lookback period
            self.rsi_highs = [x for x in self.rsi_highs if x[0] > len(self) - self.p.divergence_lookback]
        
        # Check for bullish divergence: price makes lower low but RSI makes higher low
        if len(self.price_lows) >= 2 and len(self.rsi_lows) >= 2:
            # Sort by time (most recent first)
            price_lows_sorted = sorted(self.price_lows, key=lambda x: x[0], reverse=True)
            rsi_lows_sorted = sorted(self.rsi_lows, key=lambda x: x[0], reverse=True)
            
            # Check if we have a lower low in price
            if price_lows_sorted[0][1] < price_lows_sorted[1][1]:
                # Check if we have a higher low in RSI
                if rsi_lows_sorted[0][1] > rsi_lows_sorted[1][1]:
                    # Confirm RSI was in oversold territory
                    if rsi_lows_sorted[0][1] < self.p.rsi_oversold:
                        self.divergence_bull = True
                        self.bull_divergence_signal[0] = self.data.low[0] * 0.99  # For plotting
        
        # Check for bearish divergence: price makes higher high but RSI makes lower high
        if len(self.price_highs) >= 2 and len(self.rsi_highs) >= 2:
            # Sort by time (most recent first)
            price_highs_sorted = sorted(self.price_highs, key=lambda x: x[0], reverse=True)
            rsi_highs_sorted = sorted(self.rsi_highs, key=lambda x: x[0], reverse=True)
            
            # Check if we have a higher high in price
            if price_highs_sorted[0][1] > price_highs_sorted[1][1]:
                # Check if we have a lower high in RSI
                if rsi_highs_sorted[0][1] < rsi_highs_sorted[1][1]:
                    # Confirm RSI was in overbought territory
                    if rsi_highs_sorted[0][1] > self.p.rsi_overbought:
                        self.divergence_bear = True
                        self.bear_divergence_signal[0] = self.data.high[0] * 1.01  # For plotting
    
    def next(self):
        """Main strategy logic - called for each new price bar"""
        # Skip if any order is pending
        if self.buy_order or self.sell_order:
            return
            
        # Reset plotting signals
        self.bull_divergence_signal[0] = float('nan')
        self.bear_divergence_signal[0] = float('nan')
            
        # Need enough bars for indicators before we can analyze
        min_bars_needed = self.p.rsi_period + 5
        if len(self) <= min_bars_needed:
            return
            
        # Find divergences safely
        self.find_divergences()
        
        # Current price and indicators
        price = self.data.close[0]
        current_rsi = self.rsi[0]
        
        # If we are in a position, check for exit conditions
        if self.position:
            # Early exit for long positions
            if self.position.size > 0 and current_rsi > self.p.exit_rsi_thresh:
                self.cancel_exit_orders()
                self.close()
                self.log("EXIT LONG: RSI moved above exit threshold")
            
            # Early exit for short positions
            elif self.position.size < 0 and current_rsi < self.p.exit_rsi_thresh_short:
                self.cancel_exit_orders()
                self.close()
                self.log("EXIT SHORT: RSI moved below exit threshold")
            
            return
        
        # ENTRY CONDITIONS
        
        # Check if we can trade now (throttling)
        if not self.can_trade_now():
            return
        
        # Accessing previous price safely to check crossovers
        prev_price = self.get_safe_price_value(1)
        if prev_price is None:
            return
            
        # Bullish divergence signal
        if self.divergence_bull:
            # Confirm with trend (uptrend or price crossing above SMA)
            trend_up = price > self.sma[0]
            sma_cross_up = price > self.sma[0] and prev_price < self.sma[0]
            
            if trend_up or sma_cross_up:
                # Calculate stop loss based on ATR
                stop_price = price - (self.atr[0] * self.p.stop_atr_multiple)
                # Calculate position size
                size = self.calculate_position_size(stop_price)
                
                # Enter long position
                self.log(f"BULLISH DIVERGENCE SIGNAL: RSI={current_rsi:.2f}")
                self.buy_order = self.buy(size=size)
                self.bull_divergence_signal[0] = self.data.low[0] * 0.99  # For plotting
        
        # Bearish divergence signal
        if self.divergence_bear:
            # Confirm with trend (downtrend or price crossing below SMA)
            trend_down = price < self.sma[0]
            sma_cross_down = price < self.sma[0] and prev_price > self.sma[0]
            
            if trend_down or sma_cross_down:
                # Calculate stop loss based on ATR
                stop_price = price + (self.atr[0] * self.p.stop_atr_multiple)
                # Calculate position size
                size = self.calculate_position_size(stop_price)
                
                # Enter short position
                self.log(f"BEARISH DIVERGENCE SIGNAL: RSI={current_rsi:.2f}")
                self.sell_order = self.sell(size=size)
                self.bear_divergence_signal[0] = self.data.high[0] * 1.01  # For plotting
    
    def stop(self):
        """Called when backtest is complete"""
        self.log('RSI Divergence Strategy completed')
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}')
        
        # Add a note about market conditions
        self.log('NOTE: This strategy performs best in trending markets with pullbacks')
        self.log('      where divergences signal potential trend resumption')


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='RSI Divergence Strategy with data from PostgreSQL database',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # Basic input parameters
    parser.add_argument('--data', '-d',
                        required=True,
                        help='Stock symbol to retrieve data for')
    
    parser.add_argument('--dbuser', '-u',
                        default='jason',
                        help='PostgreSQL username')
    
    parser.add_argument('--dbpass', '-pw',
                        default='fsck',
                        help='PostgreSQL password')
    
    parser.add_argument('--dbname', '-n',
                        default='market_data',
                        help='PostgreSQL database name')
    
    parser.add_argument('--fromdate', '-f',
                        default='2018-01-01',
                        help='Starting date in YYYY-MM-DD format')
    
    parser.add_argument('--todate', '-t',
                        default='2023-12-31',
                        help='Ending date in YYYY-MM-DD format')
    
    parser.add_argument('--cash', '-c',
                        default=100000.0, type=float,
                        help='Starting cash')
    
    # RSI and Divergence parameters
    parser.add_argument('--rsi-period', '-rp',
                        default=14, type=int,
                        help='RSI calculation period')
    
    parser.add_argument('--divergence-lookback', '-dl',
                        default=20, type=int,
                        help='Periods to look back for divergence')
    
    parser.add_argument('--rsi-oversold', '-ro',
                        default=30, type=int,
                        help='RSI oversold threshold')
    
    parser.add_argument('--rsi-overbought', '-rob',
                        default=70, type=int,
                        help='RSI overbought threshold')
    
    # Trend confirmation
    parser.add_argument('--trend-sma', '-ts',
                        default=50, type=int,
                        help='SMA period for trend confirmation')
    
    # Exit parameters
    parser.add_argument('--exit-rsi-thresh', '-ert',
                        default=45, type=int,
                        help='RSI threshold to exit longs')
    
    parser.add_argument('--exit-rsi-thresh-short', '-erts',
                        default=55, type=int,
                        help='RSI threshold to exit shorts')
    
    # Risk management parameters
    parser.add_argument('--risk-percent', '-rip',
                        default=1.0, type=float,
                        help='Risk per trade as percentage of portfolio')
    
    parser.add_argument('--stop-atr-multiple', '-sam',
                        default=2.0, type=float,
                        help='ATR multiplier for stop loss')
    
    parser.add_argument('--atr-period', '-ap',
                        default=14, type=int,
                        help='ATR period')
    
    parser.add_argument('--tp-sl-ratio', '-tsr',
                        default=2.0, type=float,
                        help='Take profit to stop loss ratio')
    
    # Trade throttling
    parser.add_argument('--trade-throttle-days', '-ttd',
                        default=5, type=int,
                        help='Minimum days between trades')
    
    # Plotting
    parser.add_argument('--plot', '-p', action='store_true',
                        help='Generate and show a plot of the trading activity')
    
    return parser.parse_args()


def main():
    """Main function to run the strategy"""
    args = parse_args()
    
    # Convert dates
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
    
    # Fetch data from PostgreSQL database
    try:
        df = get_db_data(args.data, args.dbuser, args.dbpass, args.dbname, fromdate, todate)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
    
    # Create data feed
    data = StockPriceData(dataname=df)
    
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Add the data feed to cerebro
    cerebro.adddata(data)
    
    # Add the strategy
    cerebro.addstrategy(
        RSIDivergenceStrategy,
        # RSI parameters
        rsi_period=args.rsi_period,
        divergence_lookback=args.divergence_lookback,
        rsi_oversold=args.rsi_oversold,
        rsi_overbought=args.rsi_overbought,
        
        # Trend confirmation
        trend_sma_period=args.trend_sma,
        
        # Exit parameters
        exit_rsi_thresh=args.exit_rsi_thresh,
        exit_rsi_thresh_short=args.exit_rsi_thresh_short,
        
        # Risk management
        risk_percent=args.risk_percent,
        stop_atr_multiple=args.stop_atr_multiple,
        atr_period=args.atr_period,
        tp_sl_ratio=args.tp_sl_ratio,
        
        # Trade throttling
        trade_throttle_days=args.trade_throttle_days,
        
        # Logging
        log_level='info'
    )
    
    # Set our desired cash start
    cerebro.broker.setcash(args.cash)
    
    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)
    
    # Set slippage to 0 (as required)
    cerebro.broker.set_slippage_perc(0.0)
    
    # Add standard analyzers
    add_standard_analyzers(cerebro)
    
    # Print out the starting conditions
    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')
    
    # Print strategy configuration
    print('\nStrategy Configuration:')
    print(f'Symbol: {args.data}')
    print(f'Date Range: {args.fromdate} to {args.todate}')
    print(f'RSI: Period={args.rsi_period}, Oversold={args.rsi_oversold}, Overbought={args.rsi_overbought}')
    print(f'Divergence Lookback: {args.divergence_lookback} bars')
    print(f'Trend Confirmation: {args.trend_sma} SMA')
    
    print('\nExit Parameters:')
    print(f'Long Exit RSI: Above {args.exit_rsi_thresh}')
    print(f'Short Exit RSI: Below {args.exit_rsi_thresh_short}')
    print(f'Stop Loss: {args.stop_atr_multiple}x ATR')
    print(f'Take Profit: {args.tp_sl_ratio}x Stop Loss Distance')
    
    print(f'\nRisk Management: {args.risk_percent}% risk per trade')
    
    if args.trade_throttle_days > 0:
        print(f'Trade Throttling: {args.trade_throttle_days} days between trades')
    
    print('\n--- Starting Backtest ---\n')
    print('*** IMPORTANT: This strategy performs best in trending markets with pullbacks ***')
    print('where divergences signal potential trend resumption\n')
    
    # Run the strategy
    results = cerebro.run()
    
    # Print final portfolio value
    final_value = cerebro.broker.getvalue()
    print(f'Final Portfolio Value: ${final_value:.2f}')
    
    # Print standard performance metrics using standardized function
    print_performance_metrics(cerebro, results)
    
    # Plot if requested
    if args.plot:
        cerebro.plot(style='candle', barup='green', bardown='red',
                    volup='green', voldown='red',
                    fill_up='green', fill_down='red',
                    plotdist=0.5, width=16, height=9)


if __name__ == '__main__':
    main()