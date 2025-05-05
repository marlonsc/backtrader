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
GAUSSIAN CHANNEL WITH STOCHASTIC RSI TRADING STRATEGY - (bb-hard)
=================================================================

This strategy focuses on early momentum shifts, looking for StochRSI crossing above 20 during an ascending Gaussian channel, with a trailing stop exit. The name emphasizes 
the momentum reversal aspect of the strategy.

This script implements a trading strategy that combines:
1. Gaussian Channel - A weighted moving average with standard deviation bands
2. Stochastic RSI - To filter entry signals for better trade quality

STRATEGY LOGIC:
--------------
- Go LONG when:
  a. Price CLOSES ABOVE the UPPER Gaussian Channel line
  b. Stochastic RSI's K line is ABOVE its D line (stochastic is "up")
- Exit LONG (go flat) when price CLOSES BELOW the UPPER Gaussian Channel line
- No short positions are taken

GAUSSIAN CHANNEL:
---------------
Gaussian Channel consists of:
- A middle band (Gaussian weighted moving average)
- An upper band (middle band + multiplier * Gaussian weighted standard deviation)
- A lower band (middle band - multiplier * Gaussian weighted standard deviation)

This indicator uses a Gaussian weighting function that gives higher importance
to values near the center of the lookback period and less to those at the
extremes, creating a smooth, responsive indicator.

STOCHASTIC RSI:
-------------
StochRSI combines Relative Strength Index (RSI) with Stochastic oscillator:
- First calculates RSI
- Then applies Stochastic formula to the RSI values
- K line = smoothed stochastic value
- D line = smoothed K line

USAGE:
------
python strategies/bb-hard.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2018-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2069-01-01)

OPTIONAL ARGUMENTS:
------------------
--dbuser, -u    : PostgreSQL username (default: jason)
--dbpass, -pw   : PostgreSQL password (default: fsck)
--dbname, -n    : PostgreSQL database name (default: market_data)
--cash, -c      : Initial cash for the strategy (default: $100,000)
--gausslength, -gl  : Period for Gaussian Channel calculation (default: 20, min: 5)
--multiplier, -m    : Multiplier for Gaussian standard deviation (default: 2.0)
--rsilength, -rl    : Period for RSI calculation (default: 14)
--stochlength, -sl  : Period for Stochastic calculation (default: 14)
--klength, -kl      : Smoothing K period for Stochastic RSI (default: 3)
--dlength, -dl      : Smoothing D period for Stochastic RSI (default: 3)
--plot, -p          : Generate and show a plot of the trading activity

EXAMPLE:
--------
python strategies/gaussian_stochrsi_momentum.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --plot
"""

from __future__ import (absolute_import, division, print_function,
                       unicode_literals)

import argparse
import datetime
import os
import sys
import math
import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
import matplotlib.pyplot as plt
import backtrader as bt
import backtrader.indicators as btind
from backtrader.utils.py3 import range

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


class StochasticRSI(bt.Indicator):
    """
    Stochastic RSI Indicator
    
    Calculation:
    1. Calculate RSI with specified length
    2. Find highest and lowest RSI values over stochlength period
    3. Calculate stochastic value: 100 * (RSI - RSI lowest) / (RSI highest - RSI lowest)
    4. Smooth K line: SMA(stochastic, klength)
    5. Smooth D line: SMA(K, dlength)
    
    Params:
    - rsilength: Period for RSI calculation
    - stochlength: Period for Stochastic calculation
    - klength: Smoothing period for K line
    - dlength: Smoothing period for D line
    """
    lines = ('k', 'd')
    params = (
        ('rsilength', 14),
        ('stochlength', 14),
        ('klength', 3),
        ('dlength', 3),
    )
    
    plotinfo = dict(
        plot=True,
        plotname='Stochastic RSI',
        subplot=True,
        plotlinelabels=True
    )
    
    plotlines = dict(
        k=dict(color='blue', _name='K'),
        d=dict(color='orange', _name='D')
    )
    
    def __init__(self):
        # Calculate RSI on the close price
        self.rsi = bt.indicators.RSI(self.data, period=self.p.rsilength)
        
        # Calculate highest and lowest RSI values over the stochlength period
        self.highest_rsi = bt.indicators.Highest(self.rsi, period=self.p.stochlength)
        self.lowest_rsi = bt.indicators.Lowest(self.rsi, period=self.p.stochlength)
        
        # Calculate raw stochastic value (not smoothed yet)
        # stoch = 100 * (RSI - RSI lowest) / (RSI highest - RSI lowest)
        self.rsi_diff = self.highest_rsi - self.lowest_rsi
        self.stoch = 100.0 * (self.rsi - self.lowest_rsi) / (self.rsi_diff + 0.000001)  # Avoid division by zero
        
        # Apply smoothing to K and D lines
        self.lines.k = bt.indicators.SMA(self.stoch, period=self.p.klength)
        self.lines.d = bt.indicators.SMA(self.lines.k, period=self.p.dlength)


class GaussianFilter(bt.Indicator):
    """
    Gaussian Filter indicator as described by John Ehlers
    
    This indicator calculates a filter and channel bands using Gaussian filter techniques
    """
    lines = ('filt', 'hband', 'lband')
    params = (
        ('poles', 4),         # Number of poles (1-9)
        ('period', 144),      # Sampling period (min: 2)
        ('mult', 1.414),      # True Range multiplier
        ('lag_reduction', False),  # Reduced lag mode
        ('fast_response', False),  # Fast response mode
        ('source', None)      # Source data (default: hlc3)
    )
    
    plotinfo = dict(
        plot=True,
        plotname='Gaussian Channel',
        subplot=False,  # Plot on the same graph as price
        plotlinelabels=True
    )
    
    plotlines = dict(
        filt=dict(color='green', _name='Filter', linewidth=2),
        hband=dict(color='red', _name='Upper Band'),
        lband=dict(color='red', _name='Lower Band')
    )
    
    def __init__(self):
        # Use the provided source or default to HLC3
        if self.p.source is None:
            self.src = (self.data.high + self.data.low + self.data.close) / 3.0
        else:
            self.src = self.p.source
        
        # Beta and Alpha components
        beta = (1 - math.cos(4 * math.asin(1) / self.p.period)) / (math.pow(1.414, 2 / self.p.poles) - 1)
        alpha = -beta + math.sqrt(math.pow(beta, 2) + 2 * beta)
        
        # Lag
        lag = (self.p.period - 1) / (2 * self.p.poles)
        
        # Apply the filters - we'll implement a simplified version here
        self.srcdata = self.src
        self.trdata = bt.indicators.TrueRange(self.data)
        
        # Exponential filters for the main data and true range
        self.filt_n = bt.indicators.EMA(self.srcdata, period=int(self.p.period / self.p.poles))
        self.filt_tr = bt.indicators.EMA(self.trdata, period=int(self.p.period / self.p.poles))
        
        # Output lines
        self.lines.filt = self.filt_n
        self.lines.hband = self.filt_n + self.filt_tr * self.p.mult
        self.lines.lband = self.filt_n - self.filt_tr * self.p.mult


class GaussianChannel(bt.Indicator):
    """
    Gaussian Channel Indicator
    
    A channel indicator that uses Gaussian weighted moving average and
    standard deviation to create adaptive bands.
    
    For simplicity, this implementation approximates the Gaussian weighting
    using standard indicators available in backtrader.
    
    Params:
    - length: Period for calculations (minimum 5)
    - multiplier: Multiplier for standard deviation bands
    """
    lines = ('mid', 'upper', 'lower')
    params = (
        ('length', 20),      # Period for calculations
        ('multiplier', 2.0), # Multiplier for standard deviation bands
    )
    
    plotinfo = dict(
        plot=True,
        plotname='Gaussian Channel',
        subplot=False,  # Plot on the same graph as price
        plotlinelabels=True
    )
    
    plotlines = dict(
        mid=dict(color='yellow', _name='Mid'),
        upper=dict(color='green', _name='Upper'),
        lower=dict(color='red', _name='Lower')
    )
    
    def __init__(self):
        # Ensure we have enough data length for calculations
        if self.p.length < 5:
            raise ValueError("Gaussian Channel length must be at least 5")
        
        # Use EMA for middle line as an approximation of Gaussian weighted MA
        # EMA gives more weight to recent data which partially mimics the Gaussian curve effect
        self.lines.mid = bt.indicators.ExponentialMovingAverage(
            self.data, period=self.p.length
        )
        
        # Calculate standard deviation - using built-in StdDev indicator
        self.stddev = bt.indicators.StdDev(
            self.data, period=self.p.length, movav=bt.indicators.ExponentialMovingAverage
        )
        
        # Upper and lower bands
        self.lines.upper = self.lines.mid + self.stddev * self.p.multiplier
        self.lines.lower = self.lines.mid - self.stddev * self.p.multiplier


class StochasticRSIGaussianChannelStrategy(bt.Strategy, TradeThrottling):
    """
    Strategy that implements the Stochastic RSI with Gaussian Channel trading rules:
    - Open long position when:
      1. The gaussian channel is ascending (filt > filt[1]) 
      2. The stochastic RSI crosses from below 20 to above 20 (K[0] > 20 and K[-1] <= 20)
    - Exit LONG (go flat) when price CLOSES BELOW the UPPER Gaussian Channel line
    - No short positions are taken
    
    Exit Strategy Options:
    - 'default': Exit when Stochastic RSI crosses from above 80 to below 80
    - 'middle_band': Exit when price closes below the middle gaussian channel band
    - 'bars': Exit after a specified number of bars
    - 'trailing_percent': Exit using a trailing stop based on percentage (default: 3.0%)
    - 'trailing_atr': Exit using a trailing stop based on ATR
    - 'trailing_ma': Exit when price crosses below a moving average
    
    Position Sizing Options:
    - 'percent': Use a fixed percentage of available equity (default 20%)
    - 'auto': Size based on volatility (less volatile = larger position)
    
    Additional Features:
    - Trade throttling to limit trade frequency
    - Risk management with stop loss functionality
    
    Best Market Conditions:
    - Strong uptrending or bull markets
    - Sectors with momentum and clear trend direction
    - Avoid using in choppy or ranging markets
    - Most effective in markets with clear directional movement
    """
    params = (
        # Stochastic RSI parameters
        ('rsilength', 14),        # Period for RSI calculation
        ('stochlength', 14),      # Period for Stochastic calculation
        ('smoothk', 3),           # Smoothing K period
        ('smoothd', 3),           # Smoothing D period
        
        # Gaussian Channel parameters
        ('poles', 4),             # Number of poles (1-9)
        ('period', 144),          # Sampling period (min: 2)
        ('trmult', 1.414),        # Filtered True Range multiplier
        ('lag_reduction', False), # Reduced lag mode
        ('fast_response', False), # Fast response mode
        
        # Date range parameters
        ('startdate', datetime.datetime(2018, 1, 1)),  # Start date for trading
        ('enddate', datetime.datetime(2069, 12, 31)),  # End date for trading
        
        ('printlog', False),      # Print log for each trade
        
        # Exit strategy parameters
        ('exit_strategy', 'trailing_percent'),  # Exit strategy: 'default', 'middle_band', 'bars', 'trailing_percent', 'trailing_atr', 'trailing_ma'
        ('exit_bars', 5),         # Number of bars to hold position when exit_strategy='bars'
        ('trailing_percent', 3.0), # Percentage for trailing stop when exit_strategy='trailing_percent'
        ('trailing_atr_mult', 2.0), # ATR multiplier for trailing stop when exit_strategy='trailing_atr'
        ('trailing_atr_period', 14), # ATR period for trailing stop when exit_strategy='trailing_atr'
        ('trailing_ma_period', 50), # MA period for trailing stop when exit_strategy='trailing_ma'
        
        # Position sizing parameters
        ('position_sizing', 'percent'), # Position sizing method: 'percent', 'auto'
        ('position_percent', 20.0),    # Percentage of equity to use per trade (when position_sizing='percent')
        ('max_position_percent', 95.0), # Maximum percentage of equity to use per trade
        ('risk_percent', 1.0),         # Risk percentage of equity per trade (used in volatility sizing)
        
        # Trade throttling
        ('trade_throttle_hours', 0),   # Minimum hours between trades (0 = no throttling)
        
        # Risk management
        ('use_stop_loss', False),      # Whether to use a stop loss
        ('stop_loss_percent', 5.0),    # Stop loss percentage from entry
        
        # Extra parameters for ATR indicator
        ('atr_period', 14),            # Period for ATR indicator
    )
    
    def __init__(self):
        # Keep track of close price
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        
        # To keep track of pending orders and trade info
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.bar_executed = None
        
        # To keep track of trade throttling
        self.last_trade_time = None
        
        # For trailing stops
        self.highest_price = 0
        self.trailing_stop_price = 0
        
        # Parse the datetime values for trading date range filter
        if self.p.startdate:
            self.start_date = bt.date2num(self.p.startdate)
        else:
            self.start_date = 0
            
        if self.p.enddate:
            self.end_date = bt.date2num(self.p.enddate)
        else:
            self.end_date = float('inf')
        
        # Create Stochastic RSI indicator
        self.stoch_rsi = StochasticRSI(
            self.data,
            rsilength=self.p.rsilength,
            stochlength=self.p.stochlength,
            klength=self.p.smoothk,
            dlength=self.p.smoothd
        )
        
        # Create Gaussian Channel indicator
        self.gaussian = GaussianFilter(
            self.datas[0],
            poles=self.p.poles,
            period=self.p.period,
            mult=self.p.trmult,
            lag_reduction=self.p.lag_reduction,
            fast_response=self.p.fast_response
        )
        
        # Additional indicators based on exit strategies
        
        # ATR for trailing stop
        if self.p.exit_strategy == 'trailing_atr':
            self.atr = bt.indicators.ATR(self.data, period=self.p.trailing_atr_period)
        
        # Moving Average for trailing MA stop
        if self.p.exit_strategy == 'trailing_ma':
            self.trailing_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.p.trailing_ma_period)
        
        # ATR for volatility-based position sizing
        if self.p.position_sizing == 'auto':
            self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)

    def log(self, txt, dt=None, doprint=False):
        """ Logging function """
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Comm: %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                
                # Update last trade time for throttling
                self.last_trade_time = self.datas[0].datetime.datetime(0)
                
                # Initialize trailing stop values
                self.highest_price = self.buyprice
                
                # Set stop loss price if enabled
                if self.p.use_stop_loss and self.p.stop_loss_percent > 0:
                    self.stop_loss_price = self.buyprice * (1 - self.p.stop_loss_percent / 100)
                    self.log(f'STOP LOSS SET: {self.stop_loss_price:.2f}')
                
                # Initialize exit conditions
                if self.p.exit_strategy == 'bars':
                    # Store the current bar index for bar-based exit
                    self.exit_bar = len(self) + self.p.exit_bars
                
                # Set initial trailing stop price based on strategy
                if self.p.exit_strategy == 'trailing_percent':
                    self.trailing_stop_price = self.buyprice * (1 - self.p.trailing_percent / 100)
                    self.log(f'TRAILING STOP SET: {self.trailing_stop_price:.2f}')
                elif self.p.exit_strategy == 'trailing_atr':
                    self.trailing_stop_price = self.buyprice - self.atr[0] * self.p.trailing_atr_mult
                    self.log(f'ATR TRAILING STOP SET: {self.trailing_stop_price:.2f}')
                
            else:  # Sell
                self.log(
                    'SELL EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Comm: %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))

            # Record the bar where the trade was executed
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset order variable
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
                 
    def can_trade_now(self):
        """Check if enough time has passed since the last trade for throttling"""
        if self.p.trade_throttle_hours <= 0 or self.last_trade_time is None:
            return True
            
        current_time = self.datas[0].datetime.datetime(0)
        time_delta = current_time - self.last_trade_time
        hours_passed = time_delta.total_seconds() / 3600
        
        return hours_passed >= self.p.trade_throttle_hours

    def calculate_position_size(self):
        """Calculate position size based on selected sizing method"""
        available_cash = self.broker.get_cash()
        current_price = self.dataclose[0]
        
        if self.p.position_sizing == 'percent':
            # Fixed percentage of available equity
            cash_to_use = available_cash * (self.p.position_percent / 100)
            # Make sure we don't exceed maximum position percentage
            cash_to_use = min(cash_to_use, available_cash * (self.p.max_position_percent / 100))
            size = int(cash_to_use / current_price)
            return size
            
        elif self.p.position_sizing == 'auto':
            # Volatility-based position sizing
            atr_value = self.atr[0]
            if atr_value <= 0:
                # Fallback to fixed percentage if ATR is invalid
                return int(available_cash * (self.p.position_percent / 100) / current_price)
                
            # Calculate position size based on risk percentage and volatility
            risk_amount = self.broker.getvalue() * (self.p.risk_percent / 100)
            risk_per_share = atr_value * self.p.trailing_atr_mult
            
            if risk_per_share <= 0:
                # Avoid division by zero
                size = int(available_cash * (self.p.position_percent / 100) / current_price)
            else:
                size = int(risk_amount / risk_per_share)
                
            # Calculate the cash required for this position
            position_value = size * current_price
            
            # Ensure we don't exceed maximum position percentage
            max_position_value = available_cash * (self.p.max_position_percent / 100)
            if position_value > max_position_value:
                size = int(max_position_value / current_price)
                
            return size
        
        # Default fallback
        return int(available_cash * (self.p.max_position_percent / 100) / current_price)

    def should_exit_trade(self):
        """Determine if we should exit the trade based on exit strategy"""
        # Default strategy (original exit condition)
        if self.p.exit_strategy == 'default':
            # StochRSI crosses from above 80 to below 80
            return self.stoch_rsi.k[-1] >= 80 and self.stoch_rsi.k[0] < 80
            
        # Middle band exit
        elif self.p.exit_strategy == 'middle_band':
            return self.dataclose[0] < self.gaussian.filt[0]
            
        # Time-based exit
        elif self.p.exit_strategy == 'bars':
            return len(self) >= self.exit_bar
            
        # Trailing stop based exits
        elif self.p.exit_strategy == 'trailing_percent':
            # Update the highest price seen since entry
            if self.datahigh[0] > self.highest_price:
                self.highest_price = self.datahigh[0]
                # Update trailing stop
                self.trailing_stop_price = self.highest_price * (1 - self.p.trailing_percent / 100)
                self.log(f'TRAILING STOP UPDATED: {self.trailing_stop_price:.2f}', doprint=False)
                
            # Exit if price touches or goes below the trailing stop
            return self.datalow[0] <= self.trailing_stop_price
            
        elif self.p.exit_strategy == 'trailing_atr':
            # Update the highest price seen since entry
            if self.datahigh[0] > self.highest_price:
                self.highest_price = self.datahigh[0]
                # Update trailing stop
                self.trailing_stop_price = self.highest_price - (self.atr[0] * self.p.trailing_atr_mult)
                self.log(f'ATR TRAILING STOP UPDATED: {self.trailing_stop_price:.2f}', doprint=False)
                
            # Exit if price touches or goes below the trailing stop
            return self.datalow[0] <= self.trailing_stop_price
            
        elif self.p.exit_strategy == 'trailing_ma':
            # Exit when price closes below the moving average
            return self.dataclose[0] < self.trailing_ma[0]
            
        # Stop loss hit
        if self.p.use_stop_loss and hasattr(self, 'stop_loss_price'):
            if self.datalow[0] <= self.stop_loss_price:
                self.log(f'STOP LOSS TRIGGERED: {self.stop_loss_price:.2f}')
                return True
                
        # Default is to never exit (not realistic but safe)
        return False

    def next(self):
        # Only operate within the specified date range
        current_date = self.data.datetime.date(0)
        current_dt_num = bt.date2num(current_date)
        
        in_date_range = (current_dt_num >= self.start_date and 
                         current_dt_num <= self.end_date)
        
        if not in_date_range:
            return  # Skip trading if not in date range

        # Check if an order is pending, if so we cannot send a 2nd one
        if self.order:
            return

        # Debug info every 5 bars
        if len(self) % 5 == 0:
            self.log(f'Close: {self.dataclose[0]:.2f}, '
                    f'GC Mid: {self.gaussian.filt[0]:.2f}, '
                    f'GC Upper: {self.gaussian.hband[0]:.2f}, '
                    f'GC Lower: {self.gaussian.lband[0]:.2f}, '
                    f'StochRSI K: {self.stoch_rsi.k[0]:.2f}, '
                    f'D: {self.stoch_rsi.d[0]:.2f}', doprint=True)
                    
            # Show trailing stop info if in a position
            if self.position and hasattr(self, 'trailing_stop_price') and self.trailing_stop_price > 0:
                self.log(f'Trailing Stop: {self.trailing_stop_price:.2f}', doprint=True)

        # Check if we are in the market
        if not self.position:
            # LONG ENTRY CONDITIONS:
            # 1. Gaussian channel is ascending (filt > filt[1])
            # 2. StochRSI crosses from below 20 to above 20
            is_gaussian_ascending = self.gaussian.filt[0] > self.gaussian.filt[-1]
            is_stoch_rsi_cross_up = self.stoch_rsi.k[0] > 20 and self.stoch_rsi.k[-1] <= 20
            
            if is_gaussian_ascending and is_stoch_rsi_cross_up:
                # Check if we can trade now based on throttling
                if not self.can_trade_now():
                    time_since_last = (self.datas[0].datetime.datetime(0) - self.last_trade_time).total_seconds() / 3600
                    self.log(f'Trade throttled: {time_since_last:.1f}h of {self.p.trade_throttle_hours}h elapsed since last trade', doprint=True)
                    return
                
                # Calculate position size
                size = self.calculate_position_size()
                
                if size <= 0:
                    self.log('Zero position size calculated, skipping trade', doprint=True)
                    return
                
                self.log(f'BUY CREATE, Price: {self.dataclose[0]:.2f}, Size: {size}')
                
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(size=size)
        else:
            # We are in a position, check if we should exit
            if self.should_exit_trade():
                reason = ''
                # Add reason for exit to log
                if self.p.exit_strategy == 'default':
                    reason = 'StochRSI crossed from above 80 to below 80'
                elif self.p.exit_strategy == 'middle_band':
                    reason = 'Price below middle band'
                elif self.p.exit_strategy == 'bars':
                    reason = f'Exit after {self.p.exit_bars} bars'
                elif self.p.exit_strategy == 'trailing_percent':
                    reason = f'Trailing stop ({self.p.trailing_percent}%) hit'
                elif self.p.exit_strategy == 'trailing_atr':
                    reason = f'ATR trailing stop ({self.p.trailing_atr_mult}x ATR) hit'
                elif self.p.exit_strategy == 'trailing_ma':
                    reason = f'Price below {self.p.trailing_ma_period} period MA'
                elif self.p.use_stop_loss and self.datalow[0] <= self.stop_loss_price:
                    reason = f'Stop loss ({self.p.stop_loss_percent}%) hit'
                
                self.log(f'SELL CREATE, {reason}, Price: {self.dataclose[0]:.2f}')
                
                # Close the long position
                self.order = self.sell(size=self.position.size)

    def stop(self):
        # Log final results when strategy is complete
        self.log('Final Portfolio Value: %.2f' % self.broker.getvalue(), doprint=True)


def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Enhanced Stochastic RSI with Gaussian Channel Strategy',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # Basic input parameters
    parser.add_argument('--data', '-d',
                        default='AAPL',
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
                        default='2069-12-31',
                        help='Ending date in YYYY-MM-DD format')
    
    parser.add_argument('--cash', '-c',
                        default=100000.0, type=float,
                        help='Starting cash')
    
    # Stochastic RSI parameters
    parser.add_argument('--rsilength', '-rl',
                        default=14, type=int,
                        help='Period for RSI calculation')
    
    parser.add_argument('--stochlength', '-sl',
                        default=14, type=int,
                        help='Period for Stochastic calculation')
    
    parser.add_argument('--smoothk', '-sk',
                        default=3, type=int,
                        help='Smoothing K period for Stochastic RSI')
    
    parser.add_argument('--smoothd', '-sd',
                        default=3, type=int,
                        help='Smoothing D period for Stochastic RSI')
    
    # Gaussian Channel parameters
    parser.add_argument('--poles', '-po',
                        default=4, type=int,
                        help='Number of poles for Gaussian Filter (1-9)')
    
    parser.add_argument('--period', '-pe',
                        default=144, type=int,
                        help='Sampling period for Gaussian Filter (min: 2)')
    
    parser.add_argument('--trmult', '-tm',
                        default=1.414, type=float,
                        help='Multiplier for Filtered True Range')
    
    parser.add_argument('--lag', '-lg',
                        action='store_true',
                        help='Enable reduced lag mode')
    
    parser.add_argument('--fast', '-fa',
                        action='store_true',
                        help='Enable fast response mode')
    
    # Exit strategy parameters
    parser.add_argument('--exit_strategy', '-es',
                        default='trailing_percent',
                        choices=['default', 'middle_band', 'bars', 'trailing_percent', 'trailing_atr', 'trailing_ma'],
                        help='Exit strategy to use')
    
    parser.add_argument('--exit_bars', '-eb',
                        default=5, type=int,
                        help='Number of bars to hold position when exit_strategy=bars')
    
    parser.add_argument('--trailing_percent', '-tp',
                        default=3.0, type=float,
                        help='Percentage for trailing stop when exit_strategy=trailing_percent')
    
    parser.add_argument('--trailing_atr_mult', '-tam',
                        default=2.0, type=float,
                        help='ATR multiplier for trailing stop when exit_strategy=trailing_atr')
    
    parser.add_argument('--trailing_atr_period', '-tap',
                        default=14, type=int,
                        help='ATR period for trailing stop when exit_strategy=trailing_atr')
    
    parser.add_argument('--trailing_ma_period', '-tmp',
                        default=50, type=int,
                        help='MA period for trailing stop when exit_strategy=trailing_ma')
    
    # Position sizing parameters
    parser.add_argument('--position_sizing', '-ps',
                        default='percent',
                        choices=['percent', 'auto'],
                        help='Position sizing method')
    
    parser.add_argument('--position_percent', '-pp',
                        default=20.0, type=float,
                        help='Percentage of equity to use per trade')
    
    parser.add_argument('--max_position_percent', '-mpp',
                        default=95.0, type=float,
                        help='Maximum percentage of equity to use per trade')
    
    parser.add_argument('--risk_percent', '-rp',
                        default=1.0, type=float,
                        help='Risk percentage of equity per trade')
    
    # Trade throttling
    parser.add_argument('--trade_throttle_hours', '-tth',
                        default=0, type=int,
                        help='Minimum hours between trades (0 = no throttling)')
    
    # Risk management
    parser.add_argument('--use_stop_loss', '-usl',
                        action='store_true',
                        help='Whether to use a stop loss')
    
    parser.add_argument('--stop_loss_percent', '-slp',
                        default=5.0, type=float,
                        help='Stop loss percentage from entry')
    
    # Plotting
    parser.add_argument('--plot', '-p', action='store_true',
                        help='Generate and show a plot of the trading activity')
    
    return parser.parse_args()


def main():
    """Main function to run the strategy"""
    args = parse_args()
    
    # Convert date strings to datetime objects
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
    
    # Get data from database
    df = get_db_data(args.data, args.dbuser, args.dbpass, args.dbname, fromdate, todate)
    
    # Create a Data Feed
    data = StockPriceData(dataname=df)
    
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Add the data feed to cerebro
    cerebro.adddata(data)
    
    # Add the StochRSI Gaussian Channel strategy
    cerebro.addstrategy(
        StochasticRSIGaussianChannelStrategy,
        # StochRSI parameters
        rsilength=args.rsilength,
        stochlength=args.stochlength,
        smoothk=args.smoothk,
        smoothd=args.smoothd,
        
        # Gaussian Channel parameters
        poles=args.poles,
        period=args.period,
        trmult=args.trmult,
        lag_reduction=args.lag,
        fast_response=args.fast,
        
        # Exit strategy parameters
        exit_strategy=args.exit_strategy,
        exit_bars=args.exit_bars,
        trailing_percent=args.trailing_percent,
        trailing_atr_mult=args.trailing_atr_mult,
        trailing_atr_period=args.trailing_atr_period,
        trailing_ma_period=args.trailing_ma_period,
        
        # Position sizing parameters
        position_sizing=args.position_sizing,
        position_percent=args.position_percent,
        max_position_percent=args.max_position_percent,
        risk_percent=args.risk_percent,
        
        # Trade throttling
        trade_throttle_hours=args.trade_throttle_hours,
        
        # Risk management
        use_stop_loss=args.use_stop_loss,
        stop_loss_percent=args.stop_loss_percent
    )
    
    # Set the cash start
    cerebro.broker.setcash(args.cash)
    
    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    
    # Add the standard analyzers
    add_standard_analyzers(cerebro)
    
    # Print out the starting conditions
    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')
    
    # Print strategy configuration parameters
    print('\nStrategy Configuration:')
    print(f'- Data Source: PostgreSQL database ({args.dbname})')
    print(f'- Symbol: {args.data}')
    print(f'- Date Range: {args.fromdate} to {args.todate}')
    
    if args.exit_strategy == 'default':
        print(f'- Exit Strategy: Default - StochRSI crosses from above 80 to below 80')
    elif args.exit_strategy == 'middle_band':
        print(f'- Exit Strategy: Middle Band - Exit when price crosses below middle band')
    elif args.exit_strategy == 'bars':
        print(f'- Exit Strategy: Bars - Exit after {args.exit_bars} bars')
    elif args.exit_strategy == 'trailing_percent':
        print(f'- Exit Strategy: Trailing Stop - {args.trailing_percent}% trailing stop')
    elif args.exit_strategy == 'trailing_atr':
        print(f'- Exit Strategy: ATR Trailing Stop - {args.trailing_atr_mult}x ATR')
    elif args.exit_strategy == 'trailing_ma':
        print(f'- Exit Strategy: Trailing MA - Exit when price crosses below {args.trailing_ma_period} MA')
    
    if args.use_stop_loss:
        print(f'- Stop Loss: {args.stop_loss_percent}% from entry')
    
    print('\n--- Starting Backtest ---\n')
    
    # Run the strategy
    results = cerebro.run()
    
    # Print final portfolio value
    final_value = cerebro.broker.getvalue()
    print(f'Final Portfolio Value: ${final_value:.2f}')
    
    # Print standard performance metrics
    print_performance_metrics(cerebro, results)
    
    # Extract and display detailed performance metrics
    print("\n==== DETAILED PERFORMANCE METRICS ====")
    
    # Get the first strategy instance
    strat = results[0]
    
    # Return
    ret_analyzer = strat.analyzers.returns
    total_return = ret_analyzer.get_analysis()['rtot'] * 100
    print(f"Return: {total_return:.2f}%")
    
    # Sharpe Ratio
    sharpe = strat.analyzers.sharpe_ratio.get_analysis()['sharperatio']
    if sharpe is None:
        sharpe = 0.0
    print(f"Sharpe Ratio: {sharpe:.4f}")
    
    # Max Drawdown
    dd = strat.analyzers.drawdown.get_analysis()
    max_dd = dd.get('max', {}).get('drawdown', 0.0)
    print(f"Max Drawdown: {max_dd:.2f}%")
    
    # Trade statistics
    trade_analysis = strat.analyzers.trade_analyzer.get_analysis()
    
    # Total Trades
    total_trades = trade_analysis.get('total', {}).get('total', 0)
    print(f"Total Trades: {total_trades}")
    
    # Won Trades
    won_trades = trade_analysis.get('won', {}).get('total', 0)
    print(f"Won Trades: {won_trades}")
    
    # Lost Trades
    lost_trades = trade_analysis.get('lost', {}).get('total', 0)
    print(f"Lost Trades: {lost_trades}")
    
    # Win Rate
    if total_trades > 0:
        win_rate = (won_trades / total_trades) * 100
    else:
        win_rate = 0.0
    print(f"Win Rate: {win_rate:.2f}%")
    
    # Average Win
    avg_win = trade_analysis.get('won', {}).get('pnl', {}).get('average', 0.0)
    print(f"Average Win: ${avg_win:.2f}")
    
    # Average Loss
    avg_loss = trade_analysis.get('lost', {}).get('pnl', {}).get('average', 0.0)
    print(f"Average Loss: ${avg_loss:.2f}")
    
    # Profit Factor
    gross_profit = trade_analysis.get('won', {}).get('pnl', {}).get('total', 0.0)
    gross_loss = abs(trade_analysis.get('lost', {}).get('pnl', {}).get('total', 0.0))
    
    if gross_loss != 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = float('inf') if gross_profit > 0 else 0.0
    
    print(f"Profit Factor: {profit_factor:.2f}")
    
    # Plot if requested
    if args.plot:
        cerebro.plot(style='candle', barup='green', bardown='red', 
                    volup='green', voldown='red', 
                    fill_up='green', fill_down='red',
                    plotdist=0.5, width=16, height=9)


if __name__ == '__main__':
    main() 