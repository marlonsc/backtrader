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
BOLLINGER BANDS MEAN REVERSION STRATEGY WITH POSTGRESQL DATABASE - (bb_mean_reversal)
===============================================================================

This strategy is a mean reversion trading system that buys when price touches the
lower Bollinger Band and sells when price touches the upper Bollinger Band or hits 
a trailing stop loss. It uses a comprehensive scoring system to evaluate potential 
mean reversion opportunities and incorporates market regime detection to identify 
favorable conditions.

STRATEGY LOGIC:
--------------
- Go LONG when mean reversion score is high enough (default: 70 or higher)
- Exit LONG when price touches the upper Bollinger Band OR hits a trailing stop loss
- Optional exit when price crosses the middle band (configurable)
- Optional fixed stop loss based on ATR (configurable)

MARKET CONDITIONS:
----------------
- Best used in SIDEWAYS or RANGE-BOUND markets
- Optional ability to filter for underlying uptrend
- Performs well in consolidation periods with clear support and resistance
- The strategy detects ranging markets automatically through Bollinger Band width analysis

BOLLINGER BANDS:
--------------
Bollinger Bands consist of:
- A middle band (typically a 20-period moving average)
- An upper band (middle band + 2 standard deviations)
- A lower band (middle band - 2 standard deviations)

These bands adapt to volatility - widening during volatile periods and 
narrowing during less volatile periods. The strategy uses this property to
identify potential mean reversion opportunities.

MEAN REVERSION SCORING:
---------------------
The strategy uses a comprehensive scoring system (0-100) to evaluate the probability
of a successful mean reversion trade by assessing multiple factors:

1. Price distance from Lower Bollinger Band (0-20 points)
   - 20 points: Price at or below lower band
   - 15 points: Price within 10% of lower band
   - 10 points: Price within 20% of lower band

2. RSI Oversold Condition (0-20 points)
   - 20 points: RSI below 30 (deeply oversold)
   - 10 points: RSI between 30-40 (moderately oversold)

3. Consecutive Bars Below Lower Band (0-15 points)
   - 3 points for each of the last 5 bars that close below the lower band
   - Measures persistence of oversold condition

4. Market Regime Detection (0-15 points)
   - 15 points: When BB width is contracting (indicating ranging market)
   - Market is considered ranging when current BB width < 90% of 20-period average

5. Volume Confirmation (0-15 points)
   - 15 points: Volume > 150% of 20-day average volume
   - 10 points: Volume > 100% of 20-day average volume

A minimum score threshold (default: 70) is required for entry, making the strategy
selective about which mean reversion opportunities to take.

TREND DETERMINATION:
------------------
The strategy can optionally filter for an underlying uptrend using moving averages:

1. Basic Uptrend Condition: 50-period SMA > 200-period SMA

2. Uptrend Slope Configuration:
   - The 'min-slope' parameter (default: 0.0) specifies the minimum required slope
   - Range: Any non-negative float (typically 0.0 to 0.5)
   - 0.0 means any positive slope is acceptable (or no slope requirement)
   - Higher values (e.g., 0.1, 0.2) require stronger uptrends
   - Slope is measured as the percentage change over 20 periods

3. Both moving averages must have slopes greater than the minimum specified

When using trend determination (via the --min-slope parameter), the strategy
becomes more selective, only taking mean reversion trades in the context of
a larger uptrend. This can improve win rates but may reduce trade frequency.

RISK MANAGEMENT:
--------------
The strategy uses Average True Range (ATR) for dynamic, volatility-adjusted stops:

1. Trailing Stop: Default 1.5x ATR below the highest price seen since entry
   - Adapts to market volatility automatically
   - Tighter in low volatility, wider in high volatility

2. Optional Fixed Stop Loss: Default 2.0x ATR below entry price
   - Provides a maximum risk per trade
   - Based on volatility at time of entry

ATR-based stops are superior to fixed percentage stops because they:
- Adapt to each market's specific volatility
- Prevent premature exits during normal price fluctuations
- Provide consistent risk management across different instruments

POSITION SIZING:
---------------
Position sizing is calculated to control risk exposure:

1. Portfolio Percentage: Default 20% of account equity per position
   - Configurable via --position-percent
   - Higher values increase potential returns but also increase risk

2. Maximum Position Limit: Default 95% of available cash
   - Prevents over-leveraging the account
   - Ensures some cash is always available

The effective position size will be the smaller of these two constraints,
ensuring proper risk management while maximizing potential returns.

USAGE:
------
python strategies/bb_mean_reversal.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2024-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2024-12-31)

DATABASE PARAMETERS:
------------------
--dbuser, -u    : PostgreSQL username (default: jason)
--dbpass, -pw   : PostgreSQL password (default: fsck)
--dbname, -n    : PostgreSQL database name (default: market_data)
--cash, -c      : Initial cash for the strategy (default: $100,000)

BOLLINGER BANDS PARAMETERS:
-------------------------
--bb-length, -bl: Period for Bollinger Bands calculation (default: 20)
                  This is the number of bars used to calculate the moving average
                  and standard deviation. Lower values are more responsive but may
                  generate more false signals.

--bb-mult, -bm  : Multiplier for standard deviation (default: 2.0)
                  Higher values create wider bands that capture more price action.
                  Lower values create tighter bands but may generate more false signals.

--matype, -mt   : Moving average type for Bollinger Bands basis (default: SMA)
                  Options: SMA (Simple), EMA (Exponential), WMA (Weighted), SMMA (Smoothed)
                  EMA and WMA respond faster to recent price changes.

MOVING AVERAGE PARAMETERS:
-------------------------
--ma1-period, -m1p : Period for the first moving average (default: 50)
                     Typically a shorter-term MA used to detect trend direction.

--ma2-period, -m2p : Period for the second moving average (default: 200)
                     Typically a longer-term MA used to confirm underlying trend.

--min-slope, -ms   : Minimum slope for uptrend determination (default: 0.0)
                     Range: 0.0 to any positive value (0.1-0.2 recommended for filtering)
                     0.0 means no minimum slope requirement
                     Higher values require stronger uptrends

RSI PARAMETERS:
-------------
--rsi-period, -rp   : Period for RSI calculation (default: 14)
                      Lower values make RSI more responsive but more volatile.

--rsi-oversold, -ro : RSI oversold threshold (default: 30)
                      Lower values (e.g. 20) are more conservative (deeper oversold).
                      Higher values (e.g. 40) are more aggressive (less oversold).

MEAN REVERSION SCORE:
-------------------
--min-score, -msc   : Minimum score required for entry (0-100, default: 70)
                      Higher values are more selective (fewer but potentially better trades).
                      Lower values are less selective (more trades but potentially lower quality).

--use-rsi-only, -uro: Use RSI as strict requirement instead of scoring system (default: False)
                      When enabled, strategy will only enter when price is below lower BB AND RSI < oversold threshold.
                      This makes the strategy behave like the bb_mean_reversal_rsi.py version.

EXIT PARAMETERS:
---------------
--exit-middle, -em  : Exit when price crosses the middle band (default: False)
                      Enables taking profits earlier when price returns to the mean.

--trail-atr, -ta    : ATR multiplier for trailing stop (default: 1.5)
                      Higher values give more room for price to fluctuate.
                      Lower values provide tighter stops but may exit trades earlier.

--use-stop, -us     : Use fixed stop loss in addition to trailing stop (default: False)
                      Provides an additional safety measure with a maximum loss limit.

--stop-atr, -sa     : ATR multiplier for fixed stop loss (default: 2.0)
                      Sets the stop loss at X times the ATR below entry price.

--use-percent-stops, -ups: Use percentage-based stops instead of ATR-based stops (default: False)
                          When enabled, trail-atr becomes percentage trailing stop and
                          stop-atr becomes percentage fixed stop loss.

POSITION SIZING:
---------------
--position-percent, -pp : Percentage of equity to use per trade (default: 20.0)
                          Controls how much of your account to risk on each position.
                          Higher values increase potential returns but also increase risk.

--max-position, -mp     : Maximum position size as percentage of equity (default: 95.0)
                          Prevents over-leveraging by limiting the maximum position size.

OTHER:
-----
--plot, -pl           : Generate and show a plot of the trading activity
                        Shows price data, indicators, and entry/exit points.

EXAMPLE COMMANDS:
---------------
1. Standard configuration - basic mean reversion:
   python strategies/bb_mean_reversal.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31

2. More aggressive settings - tighter bands with higher score threshold:
   python strategies/bb_mean_reversal.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --bbands-period 15 --bbands-dev 1.8 --min-score 80

3. Conservative settings - wider bands with strict trend confirmation:
   python strategies/bb_mean_reversal.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --bbands-period 30 --bbands-dev 2.5 --min-score 85 --require-trend

4. ATR-based stop loss configuration - adaptive volatility protection:
   python strategies/bb_mean_reversal.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --use-atr-trailing --atr-multiplier 3.0 --atr-period 20

5. Fixed percentage stop loss - predictable risk management:
   python strategies/bb_mean_reversal.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --use-percent-stops --stop-loss-percent 2.5 --trail-percent 5.0

6. RSI filter with middle band exit - faster mean reversion:
   python strategies/bb_mean_reversal.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --rsi-period 10 --rsi-upper 75 --rsi-lower 25 --exit-on-middle
"""

from __future__ import (absolute_import, division, print_function,
                       unicode_literals)

import argparse
import datetime
import os
import sys
import pandas as pd
import numpy as np
import psycopg2
import psycopg2.extras
import matplotlib.pyplot as plt
import backtrader as bt
import backtrader.indicators as btind

# Add the parent directory to the path so that 'strategies' can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility functions
from strategies.utils import (get_db_data, print_performance_metrics, 
                            add_standard_analyzers, TradeThrottling)


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


# Create a custom BBWidth indicator because backtrader doesn't have one built-in
class BBWidth(bt.Indicator):
    """
    Bollinger Bands Width Indicator
    
    Formula: (Upper Band - Lower Band) / Middle Band
    
    This indicator helps identify when volatility is expanding or contracting.
    """
    lines = ('bbwidth',)
    params = dict(period=20, devfactor=2.0, movav=bt.indicators.SMA)
    
    def __init__(self):
        # Calculate Bollinger Bands
        self.bband = bt.indicators.BollingerBands(
            self.data, 
            period=self.p.period,
            devfactor=self.p.devfactor,
            movav=self.p.movav
        )
        
        # Calculate BBWidth: (Upper - Lower) / Middle
        self.lines.bbwidth = (self.bband.top - self.bband.bot) / self.bband.mid


class BollingerBandStrategy(bt.Strategy, TradeThrottling):
    """
    Bollinger Bands Mean Reversion Strategy with Trend Filter

    This strategy attempts to capture mean reversion moves by:
    1. Buying when price touches or crosses below the lower Bollinger Band and the trend is up
    2. Selling when price touches or crosses above the upper Bollinger Band or hits a trailing stop loss
    
    The trend filter ensures we only take mean reversion trades in the direction of the larger trend,
    which improves the win rate and helps avoid mean reversion traps in strongly trending markets.
    
    Additional exit mechanisms include:
    - Optional exit when price crosses the middle Bollinger Band
    - Optional fixed stop loss to limit potential losses
    - Trailing stop loss to protect profits
    
    Strategy Logic:
    - Buy when price touches or crosses below lower Bollinger Band in favorable conditions
    - Sell when price touches or crosses above upper Bollinger Band or hits a trailing stop
    - Implements cool down period to avoid overtrading in volatile conditions
    - Uses risk-based position sizing to manage exposure
    
    Best Market Conditions:
    - Sideways or ranging markets with clear support and resistance
    - Markets with regular mean reversion tendencies
    - Low to moderate volatility environments
    - Avoid using in strong trending markets without appropriate filters
    """

    params = (
        # Bollinger Bands parameters
        ('bbands_period', 20),      # Period for Bollinger Bands
        ('bbands_dev', 2.0),        # Standard deviations for Bollinger Bands
        ('bbands_matype', 'SMA'),   # Moving average type for Bollinger Bands
        
        # Moving average parameters for trend determination
        ('ma1_period', 50),         # Fast moving average period
        ('ma2_period', 200),        # Slow moving average period
        ('min_slope', 0.0),         # Minimum slope for moving averages to consider trending
        
        # Entry parameters
        ('entry_band_pct', 0.0),    # Entry when price crosses below lower band - x%
        ('min_score', 70),          # Minimum mean reversion score to enter (0-100)
        ('require_trend', False),   # Whether to require an uptrend for long entries
        ('volume_factor', 1.0),     # Volume factor for entry confirmation
        
        # Exit parameters
        ('exit_on_middle', False),  # Exit when price crosses middle band
        ('exit_band_pct', 0.0),     # Exit when price crosses above upper band + x%
        
        # ATR parameters for volatility-based stops
        ('atr_period', 14),         # Period for ATR calculation
        ('atr_multiplier', 2.0),    # ATR multiplier for stop loss
        ('use_atr_trailing', True), # Use ATR for trailing stop
        
        # Fixed percentage stop parameters
        ('use_percent_stops', False), # Use fixed percentage stops instead of ATR
        ('stop_loss_percent', 3.0),   # Fixed stop loss percentage
        ('trail_percent', 4.0),       # Fixed trailing stop percentage
        
        # Position sizing parameters
        ('position_size', 0.2),       # Percentage of portfolio to use per position
        ('max_position_size', 0.5),   # Maximum position size as percentage of portfolio
        
        # Trade throttling
        ('trade_throttle_days', 5),   # Minimum days between trades
        
        # RSI parameters
        ('rsi_period', 14),         # Period for RSI calculation
        ('rsi_overbought', 70),     # Overbought threshold for RSI
        ('rsi_oversold', 30),       # Oversold threshold for RSI
        ('use_rsi_only', False),    # Use only RSI for entry signals
        
        # Other parameters
        ('printlog', False),        # Print log to console
        ('log_level', 'info'),      # Logging level: 'debug', 'info'
    )

    def log(self, txt, dt=None, level='info'):
        """
        Logging function for the strategy
        """
        if level == 'debug' and self.p.log_level != 'debug':
            return
            
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')

    def __init__(self):
        # Store the close price reference
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        # To keep track of pending orders and position cost/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # Stop loss and trailing stop values
        self.stop_price = None
        self.trail_price = None
        
        # For trade throttling
        self.last_trade_date = None
        
        # Track order and position state
        self.entry_price = None
        self.highest_price = None
        
        # Initialize trade tracking
        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # Get parameter options
        self.use_rsi_only = self.p.use_rsi_only if hasattr(self.p, 'use_rsi_only') else False
        self.use_percent_stops = self.p.use_percent_stops if hasattr(self.p, 'use_percent_stops') else False
        self.rsi_oversold = self.p.rsi_oversold if hasattr(self.p, 'rsi_oversold') else 30
        self.min_score = self.p.min_score if hasattr(self.p, 'min_score') else 70
        
        # Create Bollinger Bands indicator
        # First determine the MA type to use
        if self.p.bbands_matype == 'SMA':
            ma_class = bt.indicators.SimpleMovingAverage
        elif self.p.bbands_matype == 'EMA':
            ma_class = bt.indicators.ExponentialMovingAverage
        elif self.p.bbands_matype == 'WMA':
            ma_class = bt.indicators.WeightedMovingAverage
        elif self.p.bbands_matype == 'SMMA':
            ma_class = bt.indicators.SmoothedMovingAverage
        else:
            # Default to SMA
            ma_class = bt.indicators.SimpleMovingAverage
            
        # Calculate the Bollinger Bands
        self.bbands = bt.indicators.BollingerBands(
            self.datas[0], 
            period=self.p.bbands_period,
            devfactor=self.p.bbands_dev,
            movav=ma_class
        )
        
        # Extract individual Bollinger Band components
        self.upper_band = self.bbands.top
        self.middle_band = self.bbands.mid
        self.lower_band = self.bbands.bot
        
        # Create the trend-determining moving averages
        self.ma1 = bt.indicators.SimpleMovingAverage(
            self.datas[0],
            period=self.p.ma1_period
        )
        
        self.ma2 = bt.indicators.SimpleMovingAverage(
            self.datas[0],
            period=self.p.ma2_period
        )
        
        # Create slope indicators for the moving averages (to determine trend direction)
        # We'll calculate a simple slope using the current value and the value N bars ago
        self.ma1_slope = bt.indicators.PercentChange(
            self.ma1, period=20
        )
        
        self.ma2_slope = bt.indicators.PercentChange(
            self.ma2, period=20
        )
        
        # Crossover indicators for entry and exit conditions
        self.price_cross_lower = bt.indicators.CrossDown(self.dataclose, self.lower_band)
        self.price_cross_upper = bt.indicators.CrossUp(self.dataclose, self.upper_band)
        self.price_cross_middle = bt.indicators.CrossUp(self.dataclose, self.middle_band)

        # Add RSI for oversold/overbought conditions
        self.rsi = bt.indicators.RSI(self.datas[0], period=self.p.rsi_period)
        
        # Add ATR for stop loss and volatility assessment
        self.atr = bt.indicators.ATR(self.datas[0], period=14)
        
        # Add volume indicators for confirmation
        self.volume_ma = bt.indicators.SMA(self.datas[0].volume, period=20)
        
        # Calculate BB width for market regime detection
        self.bb_width = BBWidth(
            self.datas[0], 
            period=self.p.bbands_period,
            devfactor=self.p.bbands_dev,
            movav=ma_class
        )
        
        # Calculate 20-period average of BB Width for comparison
        self.bb_width_avg = bt.indicators.SMA(self.bb_width.bbwidth, period=20)

    def is_uptrend(self):
        """
        Determine if the market is in an uptrend based on moving averages
        """
        # Need at least ma2_period bars of data
        if len(self) <= self.p.ma2_period:
            return False
            
        # Basic uptrend condition: ma1 > ma2
        basic_uptrend = self.ma1[0] > self.ma2[0]
        
        # Check if we need to consider slope
        if self.p.min_slope > 0:
            # Only consider it an uptrend if both MAs have positive slopes greater than min_slope
            slope_ok = (self.ma1_slope[0] >= self.p.min_slope and 
                        self.ma2_slope[0] >= self.p.min_slope)
            return basic_uptrend and slope_ok
        else:
            # If min_slope is 0 or negative, only consider the basic condition
            return basic_uptrend

    def is_ranging_market(self):
        """
        Detect if market is in a sideways/ranging state based on BB width
        """
        # We need some history to establish a baseline
        if len(self) <= 20:
            return False
        
        # If current BB width is less than 90% of recent average, 
        # the market might be consolidating/ranging
        return self.bb_width.bbwidth[0] < self.bb_width_avg[0] * 0.9

    def mean_reversion_score(self):
        """
        Calculate probability of successful mean reversion
        Returns a score from 0-100, where higher values indicate
        better conditions for mean reversion
        """
        if len(self) <= 20:
            return 0
        
        score = 0
        bb_pct = 0
        
        # Calculate BB percentage band position
        bb_range = self.upper_band[0] - self.lower_band[0]
        if bb_range != 0:
            bb_pct = (self.dataclose[0] - self.lower_band[0]) / bb_range
        
        # Price distance from lower BB (0-20 points)
        if bb_pct <= 0.0:
            score += 20
        elif bb_pct <= 0.1:
            score += 15
        elif bb_pct <= 0.2:
            score += 10
        
        # Number of consecutive bars below lower band (0-15 points)
        below_band_count = 0
        for i in range(5):
            if i < len(self.dataclose) and i < len(self.lower_band):
                if self.dataclose[-i] < self.lower_band[-i]:
                    below_band_count += 1
        
        score += below_band_count * 3
        
        # RSI oversold condition (0-20 points)
        if self.rsi[0] < 30:
            score += 20
        elif self.rsi[0] < 40:
            score += 10
        
        # Ranging market (0-15 points)
        if self.is_ranging_market():
            score += 15
        
        # Volume confirmation (0-15 points)
        if self.datavolume[0] > self.volume_ma[0] * 1.5:
            score += 15
        elif self.datavolume[0] > self.volume_ma[0]:
            score += 10
        
        # Add points for uptrend if we want to integrate with trend (0-15 points)
        # Removed because we're focusing on pure mean reversion
        # if self.is_uptrend():
        #    score += 15
        
        # Return probability (0-100%)
        return min(score, 100)

    def calculate_position_size(self, price, value):
        """Calculate how many shares to buy based on position sizing rules"""
        available_cash = self.broker.get_cash()
        current_price = price
        
        # Fixed percentage of available equity
        cash_to_use = value * self.p.position_size
        
        # Make sure we don't exceed maximum available cash
        max_cash = available_cash * 0.95  # Don't use more than 95% of available cash
        cash_to_use = min(cash_to_use, max_cash)
        
        # Calculate number of shares (integer)
        size = int(cash_to_use / current_price)
        
        return size

    def next(self):
        # If an order is pending, we cannot send a new one
        if self.order:
            return
            
        # Check if we are in the market
        if not self.position:
            # BUY LOGIC
            
            # Check if we're allowed to trade based on the throttling rules
            if not self.can_trade_now():
                return
                
            # Get the mean reversion score
            score = self.mean_reversion_score()
            self.log(f'Mean reversion score: {score:.2f}', level='debug')
            
            # Check if we should enter a trade
            if score >= self.min_score:
                # Calculate position size
                size = self.calculate_position_size(self.dataclose[0], self.broker.getvalue())
                
                if size > 0:
                    self.log(f'BUY CREATE: {self.dataclose[0]:.2f}, Size: {size}, Score: {score:.1f}')
                    self.order = self.buy(size=size)
                    
                    # Update the last trade date for throttling
                    self.last_trade_date = self.datas[0].datetime.date(0)
        else:
            # If we are in a position, check for exit conditions
            
            # Exit when price touches or crosses upper band
            if self.price_cross_upper[0]:
                self.log(f'SELL CREATE: Upper band {self.upper_band[0]:.2f} touched')
                self.order = self.sell()
                return
                
            # Exit on middle band cross if enabled
            if self.p.exit_on_middle and self.price_cross_middle[0]:
                self.log(f'SELL CREATE: Middle band {self.middle_band[0]:.2f} crossed')
                self.order = self.sell()
                return
                
            # Check for stop loss hit
            if self.stop_price is not None and self.datalow[0] <= self.stop_price:
                self.log(f'SELL CREATE: Stop loss {self.stop_price:.2f} hit')
                self.order = self.sell()
                return
                
            # Update trailing stop if enabled
            if self.trail_price is not None:
                # Update the highest price seen
                if self.datahigh[0] > self.highest_price:
                    self.highest_price = self.datahigh[0]
                    
                    # Calculate new trail price
                    if self.p.use_percent_stops:
                        # Percentage-based trailing stop
                        new_trail = self.highest_price * (1 - self.p.trail_percent / 100)
                    else:
                        # ATR-based trailing stop
                        new_trail = self.highest_price - (self.atr[0] * self.p.atr_multiplier)
                        
                    # Only update if the new trail price is higher
                    if new_trail > self.trail_price:
                        self.trail_price = new_trail
                        self.log(f'Trailing stop updated to {self.trail_price:.2f}', level='debug')
                        
                # Check if trailing stop is hit
                if self.datalow[0] <= self.trail_price:
                    self.log(f'SELL CREATE: Trailing stop {self.trail_price:.2f} hit')
                    self.order = self.sell()
                    return

    def stop(self):
        """Called when backtest is finished"""
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}')
        
        # Calculate and log statistics
        if self.trade_count > 0:
            win_rate = (self.winning_trades / self.trade_count) * 100
            self.log(f'Trade Statistics: {self.trade_count} trades, {win_rate:.2f}% win rate')
        else:
            self.log('No trades executed during the backtest period')
        
        # Extra information about strategy
        self.log(f'Strategy Settings: BB({self.p.bbands_period}, {self.p.bbands_dev}), ' + 
                f'MAs({self.p.ma1_period}, {self.p.ma2_period}), Trail Stop: {self.p.trail_percent}%')

    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            # Order pending, do nothing
            return

        # Check if order was completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: Price: {order.executed.price:.2f}, Size: {order.executed.size}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            else:  # sell
                self.log(f'SELL EXECUTED: Price: {order.executed.price:.2f}, Size: {order.executed.size}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected: {order.status}')
        
        # Reset order status
        self.order = None

    def notify_trade(self, trade):
        """Track completed trades"""
        if not trade.isclosed:
            return
        
        self.trade_count += 1
        
        # Track win/loss
        if trade.pnlcomm > 0:
            self.winning_trades += 1
        elif trade.pnlcomm < 0:
            self.losing_trades += 1
        
        self.log(f'TRADE COMPLETED: PnL: Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')


def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Bollinger Bands Mean Reversion Strategy with Trend Filter',
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
                        default='2024-01-01',
                        help='Starting date in YYYY-MM-DD format')
    
    parser.add_argument('--todate', '-t',
                        default='2024-12-31',
                        help='Ending date in YYYY-MM-DD format')
    
    parser.add_argument('--cash', '-c',
                        default=100000.0, type=float,
                        help='Starting cash')
    
    # Bollinger Bands parameters
    parser.add_argument('--bb-length', '-bl',
                        default=20, type=int,
                        help='Period for Bollinger Bands calculation')
    
    parser.add_argument('--bb-mult', '-bm',
                        default=2.0, type=float,
                        help='Multiplier for standard deviation')
    
    parser.add_argument('--matype', '-mt',
                        default='SMA',
                        choices=['SMA', 'EMA', 'WMA', 'SMMA'],
                        help='Moving average type for Bollinger Bands basis')
    
    # Moving Average parameters
    parser.add_argument('--ma1-period', '-m1p',
                        default=50, type=int,
                        help='Period for first moving average (50-day)')
    
    parser.add_argument('--ma2-period', '-m2p',
                        default=200, type=int,
                        help='Period for second moving average (200-day)')
    
    parser.add_argument('--min-slope', '-ms',
                        default=0.0, type=float,
                        help='Minimum slope for uptrend determination')
    
    # RSI parameters
    parser.add_argument('--rsi-period', '-rp',
                        default=14, type=int,
                        help='Period for RSI calculation')
    
    parser.add_argument('--rsi-oversold', '-ro',
                        default=30, type=int,
                        help='RSI oversold threshold')
    
    parser.add_argument('--min-score', '-msc',
                        default=70, type=int,
                        help='Minimum mean reversion score for entry (0-100)')
    
    # Strategy mode options
    parser.add_argument('--use-rsi-only', '-uro',
                        action='store_true',
                        help='Use RSI as strict requirement instead of scoring system')
    
    parser.add_argument('--use-percent-stops', '-ups',
                        action='store_true',
                        help='Use percentage-based stops instead of ATR-based stops')
    
    # Exit parameters
    parser.add_argument('--exit-middle', '-em',
                        action='store_true',
                        help='Exit when price crosses the middle band')
    
    parser.add_argument('--trail-atr', '-ta',
                        default=1.5, type=float,
                        help='ATR multiplier for trailing stop')
    
    parser.add_argument('--use-stop', '-us',
                        action='store_true',
                        help='Use fixed stop loss in addition to trailing stop')
    
    parser.add_argument('--stop-atr', '-sa',
                        default=2.0, type=float,
                        help='ATR multiplier for fixed stop loss')
    
    # Position sizing parameters
    parser.add_argument('--position-percent', '-pp',
                        default=20.0, type=float,
                        help='Percentage of equity to use per trade')
    
    parser.add_argument('--max-position', '-mp',
                        default=95.0, type=float,
                        help='Maximum percentage of equity to use')
    
    # Trade throttling
    parser.add_argument('--trade-throttle-days', '-ttd',
                        default=5, type=int,
                        help='Minimum days between trades')
    
    # Plotting
    parser.add_argument('--plot', '-pl',
                        action='store_true',
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
    
    # Add the Bollinger Band strategy
    cerebro.addstrategy(
        BollingerBandStrategy,
        bbands_period=args.bb_length,
        bbands_dev=args.bb_mult,
        bbands_matype=args.matype,
        ma1_period=args.ma1_period,
        ma2_period=args.ma2_period,
        min_slope=args.min_slope,
        rsi_period=args.rsi_period,
        rsi_oversold=args.rsi_oversold,
        min_score=args.min_score,
        use_rsi_only=args.use_rsi_only,
        exit_on_middle=args.exit_middle,
        trail_percent=args.trail_atr,
        use_percent_stops=args.use_percent_stops,
        position_size=args.position_percent / 100.0,
        max_position_size=args.max_position / 100.0,
        trade_throttle_days=args.trade_throttle_days
    )
    
    # Set our desired cash start
    cerebro.broker.setcash(args.cash)
    
    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)
    
    # Set slippage to 0 (as required)
    cerebro.broker.set_slippage_perc(0.0)
    
    # Add standard analyzers with names expected by print_performance_metrics
    add_standard_analyzers(cerebro)
    
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
                    fill_up='green', fill_down='red')


if __name__ == '__main__':
    main()
