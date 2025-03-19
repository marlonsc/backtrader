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
BOLLINGER BANDS MEAN REVERSION STRATEGY WITH POSTGRESQL DATABASE - (bb_mean_reversal_rsi)
===============================================================================

This strategy is a mean reversion trading system that buys when price touches the
lower Bollinger Band and RSI is oversold, then sells when price touches the upper 
Bollinger Band and RSI is overbought. It's designed to capture price movements in 
range-bound or sideways markets.

STRATEGY LOGIC:
--------------
- Go LONG when price CLOSES BELOW the LOWER Bollinger Band AND RSI < 30 (oversold)
- Exit LONG when price CLOSES ABOVE the UPPER Bollinger Band AND RSI > 70 (overbought)
- Or exit when price crosses the middle band (optional)
- Optional stop-loss below the recent swing low

MARKET CONDITIONS:
----------------
*** THIS STRATEGY IS SPECIFICALLY DESIGNED FOR SIDEWAYS/RANGING MARKETS ***
- PERFORMS BEST: In markets with clear overbought and oversold levels
- AVOID USING: During strong trending markets where price can remain in extreme territories
- IDEAL TIMEFRAMES: 1-hour, 4-hour, and daily charts
- OPTIMAL MARKET CONDITION: Range-bound markets with clear support and resistance levels

The strategy will struggle in trending markets as prices can remain overbought/oversold
for extended periods, resulting in premature exit signals or false entry signals.
It performs best when price oscillates within a defined range.

This strategy can experience significant drawdowns when trading in strong trends as
Bollinger Bands expand with increasing volatility, pushing prices to extreme levels.
During such periods, the strategy might continue to try to "catch a falling knife"
or exit profitable trades too early.

RISK MANAGEMENT CONSIDERATIONS:
-----------------------------
- Consider using wider stop losses in volatile markets
- In strongly trending markets, consider disabling this strategy or using a trend filter
- Setting the RSI thresholds to more extreme values (20/80) can reduce false signals
- The exit_middle parameter can help secure profits faster, reducing the risk of reversals

BOLLINGER BANDS:
--------------
Bollinger Bands consist of:
- A middle band (typically a 20-period moving average)
- An upper band (middle band + 2 standard deviations)
- A lower band (middle band - 2 standard deviations)

These bands adapt to volatility - widening during volatile periods and 
narrowing during less volatile periods.

RSI (RELATIVE STRENGTH INDEX):
----------------------------
- Oscillator that measures momentum
- Ranges from 0 to 100
- Values below 30 typically indicate oversold conditions
- Values above 70 typically indicate overbought conditions

USAGE:
------
python strategies/bb_mean_reversal_rsi.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

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
--bb-mult, -bm  : Multiplier for standard deviation (default: 2.0)
--matype, -mt   : Moving average type for Bollinger Bands basis (default: SMA, options: SMA, EMA, WMA, SMMA)

RSI PARAMETERS:
-------------
--rsi-period, -rp: Period for RSI calculation (default: 14)
--rsi-oversold, -ro: RSI oversold threshold (default: 30)
--rsi-overbought, -rob: RSI overbought threshold (default: 70)

EXIT PARAMETERS:
---------------
--exit-middle, -em: Exit when price crosses the middle band (default: False)
--use-stop, -us : Use stop loss (default: False) 
--stop-pct, -sp : Stop loss percentage (default: 2.0)
--use-trail, -ut : Enable trailing stop loss (default: False)
--trail-pct, -tp : Trailing stop percentage (default: 2.0)

POSITION SIZING:
---------------
--risk-percent, -riskp  : Percentage of equity to risk per trade (default: 1.0)
--max-position, -mp  : Maximum position size as percentage of equity (default: 20.0)

TRADE THROTTLING:
---------------
--trade-throttle-days, -ttd : Minimum days between trades (default: 1)

OTHER:
-----
--plot, -p     : Generate and show a plot of the trading activity

EXAMPLE COMMANDS:
---------------
1. Standard configuration - classic RSI mean reversion:
   python strategies/bb_mean_reversal_rsi.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31

2. More sensitive settings - tighter bands with closer RSI thresholds:
   python strategies/bb_mean_reversal_rsi.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --bb-length 15 --bb-mult 1.8 --rsi-oversold 35 --rsi-overbought 65

3. Extreme oversold/overbought thresholds - fewer but stronger signals:
   python strategies/bb_mean_reversal_rsi.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --rsi-oversold 25 --rsi-overbought 75

4. Middle-band exit approach - quicker profit taking:
   python strategies/bb_mean_reversal_rsi.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --exit-middle

5. Conservative risk management - stop loss and trailing protection:
   python strategies/bb_mean_reversal_rsi.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --use-stop --stop-pct 2.0 --use-trail --trail-pct 1.5 --risk-percent 0.5

EXAMPLE:
--------
python strategies/bb_mean_reversal_rsi.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --exit-middle --use-stop --stop-pct 2.5 --plot
"""

from __future__ import (absolute_import, division, print_function,
                       unicode_literals)

import argparse
import datetime
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import backtrader as bt
import backtrader.indicators as btind
import psycopg2

# Add the parent directory to the path so that 'strategies' can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import from strategies.utils
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


class BollingerMeanReversionStrategy(bt.Strategy, TradeThrottling):
    """
    Bollinger Bands Mean Reversion Strategy with RSI Filter

    This strategy attempts to capture mean reversion moves by:
    1. Buying when price touches or crosses below the lower Bollinger Band AND RSI < 30
    2. Selling when price touches or crosses above the upper Bollinger Band AND RSI > 70
    
    Additional exit mechanisms include:
    - Optional exit when price crosses the middle Bollinger Band
    - Optional stop loss to limit potential losses
    - Optional trailing stop loss to lock in profits
    
    ** IMPORTANT: This strategy is specifically designed for sideways/ranging markets **
    It performs poorly in trending markets where prices can remain overbought or oversold
    for extended periods.
    """

    params = (
        # Bollinger Bands parameters
        ('bb_length', 20),        # Period for Bollinger Bands calculation
        ('bb_mult', 2.0),         # Number of standard deviations
        ('ma_type', 'SMA'),       # Moving average type
        
        # RSI parameters
        ('rsi_period', 14),       # Period for RSI calculation
        ('rsi_oversold', 30),     # RSI oversold threshold
        ('rsi_overbought', 70),   # RSI overbought threshold
        
        # Exit parameters
        ('exit_middle', False),    # Whether to exit when price crosses middle band
        ('use_stop', False),       # Whether to use fixed stop loss
        ('stop_pct', 2.0),         # Stop loss percentage
        ('use_trail', False),      # Use trailing stop loss
        ('trail_pct', 2.0),        # Trailing stop percentage
        
        # Position sizing parameters
        ('risk_percent', 1.0),     # Percentage of equity to risk per trade
        ('max_position', 20.0),    # Maximum position size as percentage
        
        # Trade throttling
        ('trade_throttle_days', 1), # Minimum days between trades

        # Logging
        ('log_level', 'info'),     # Logging level: 'debug', 'info'
    )

    def log(self, txt, dt=None, level='info'):
        """Logging function"""
        if level == 'debug' and self.p.log_level != 'debug':
            return
            
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')

    def __init__(self):
        # Store references to price data
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        
        # Order and position tracking
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.stop_price = None
        self.trail_price = None
        self.highest_price = None
        
        # For trade throttling
        self.last_trade_date = None
        
        # Determine MA type for Bollinger Bands
        if self.p.ma_type == 'SMA':
            ma_class = bt.indicators.SimpleMovingAverage
        elif self.p.ma_type == 'EMA':
            ma_class = bt.indicators.ExponentialMovingAverage
        elif self.p.ma_type == 'WMA':
            ma_class = bt.indicators.WeightedMovingAverage
        elif self.p.ma_type == 'SMMA':
            ma_class = bt.indicators.SmoothedMovingAverage
        else:
            # Default to SMA
            ma_class = bt.indicators.SimpleMovingAverage
            
        # Create Bollinger Bands
        self.bbands = bt.indicators.BollingerBands(
            self.datas[0], 
            period=self.p.bb_length,
            devfactor=self.p.bb_mult,
            movav=ma_class
        )
        
        # Create RSI indicator
        self.rsi = bt.indicators.RSI(
            self.datas[0],
            period=self.p.rsi_period
        )
        
        # Create crossover indicators for signal generation
        self.price_cross_lower = bt.indicators.CrossDown(
            self.dataclose, self.bbands.lines.bot
        )
        
        self.price_cross_upper = bt.indicators.CrossUp(
            self.dataclose, self.bbands.lines.top
        )
        
        self.price_cross_middle = bt.indicators.CrossUp(
            self.dataclose, self.bbands.lines.mid
        )
        
        # Add ATR for stop loss calculation
        self.atr = bt.indicators.ATR(self.datas[0], period=14)

    def calculate_position_size(self):
        """Calculate position size based on risk percentage"""
        cash = self.broker.getcash()
        value = self.broker.getvalue()
        current_price = self.dataclose[0]
        
        # Calculate size based on risk percentage
        risk_amount = value * (self.p.risk_percent / 100)
        risk_per_share = current_price * (self.p.stop_pct / 100)
        
        if risk_per_share > 0:
            size = int(risk_amount / risk_per_share)
        else:
            # Fallback calculation based on max position
            size = int((value * self.p.max_position / 100) / current_price)
        
        # Make sure we don't exceed maximum position size
        max_size = int((cash * self.p.max_position / 100) / current_price)
        return min(size, max_size)

    def next(self):
        # If an order is pending, we cannot send a new one
        if self.order:
            return
            
        # Check for trailing stop if enabled
        if self.position and self.p.use_trail and self.trail_price is not None:
            # Update the trailing stop if price moves higher
            if self.datahigh[0] > self.highest_price:
                self.highest_price = self.datahigh[0]
                self.trail_price = self.highest_price * (1.0 - self.p.trail_pct / 100.0)
                self.log(f'Trailing stop updated to: {self.trail_price:.2f}', level='debug')
            
            # Check if trailing stop is hit
            if self.datalow[0] <= self.trail_price:
                self.log(f'TRAILING STOP TRIGGERED: Price: {self.datalow[0]:.2f}, Stop: {self.trail_price:.2f}')
                self.order = self.sell()
                return
        
        # Check for stop loss if we're in the market and stop loss is enabled
        if self.position and self.p.use_stop and self.stop_price is not None:
            if self.datalow[0] < self.stop_price:
                self.log(f'STOP LOSS TRIGGERED: Price: {self.datalow[0]:.2f}, Stop: {self.stop_price:.2f}')
                self.order = self.close()
                return
                
        # Check for price crossing middle band if exit_middle is enabled
        if self.position and self.p.exit_middle and self.price_cross_middle[0]:
            self.log(f'MIDDLE BAND EXIT: Price: {self.dataclose[0]:.2f}, Middle Band: {self.bbands.lines.mid[0]:.2f}')
            self.order = self.close()
            return
        
        # If we are in the market, look for a sell signal
        if self.position:
            # Sell if price crosses upper band and RSI > overbought threshold
            if self.price_cross_upper[0] and self.rsi[0] > self.p.rsi_overbought:
                self.log(f'SELL SIGNAL: Price: {self.dataclose[0]:.2f}, Upper Band: {self.bbands.lines.top[0]:.2f}, RSI: {self.rsi[0]:.1f}')
                self.order = self.close()
        
        # If we are not in the market, look for a buy signal
        else:
            # Check if we can trade now (throttling)
            if not self.can_trade_now():
                return
                
            # Buy if price crosses lower band and RSI < oversold threshold
            if self.price_cross_lower[0] and self.rsi[0] < self.p.rsi_oversold:
                # Calculate position size
                size = self.calculate_position_size()
                
                self.log(f'BUY SIGNAL: Price: {self.dataclose[0]:.2f}, Lower Band: {self.bbands.lines.bot[0]:.2f}, RSI: {self.rsi[0]:.1f}')
                
                if size > 0:
                    self.order = self.buy(size=size)
                    
                    # Set stop loss price if enabled
                    if self.p.use_stop:
                        self.stop_price = self.dataclose[0] * (1.0 - self.p.stop_pct / 100.0)
                        self.log(f'Stop loss set at {self.stop_price:.2f}')
                    
                    # Set trailing stop if enabled
                    if self.p.use_trail:
                        self.highest_price = self.dataclose[0]
                        self.trail_price = self.dataclose[0] * (1.0 - self.p.trail_pct / 100.0)
                        self.log(f'Initial trailing stop set at {self.trail_price:.2f}')
                    
                    # Update last trade date for throttling
                    self.last_trade_date = self.datas[0].datetime.date(0)

    def stop(self):
        """Called when backtest is complete"""
        self.log('Bollinger Bands Mean Reversion Strategy completed')
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}')
        
        # Add a note about market conditions
        self.log('NOTE: This strategy is specifically designed for SIDEWAYS/RANGING MARKETS')
        self.log('      It performs poorly in trending markets where price can remain at extremes')
        self.log('      Ideal conditions: Price oscillating between support and resistance levels')

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
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
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
        
        self.log(f'TRADE COMPLETED: PnL: Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Bollinger Bands Mean Reversion Strategy with RSI Filter',
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
    
    # RSI parameters
    parser.add_argument('--rsi-period', '-rp',
                       default=14, type=int,
                       help='Period for RSI calculation')
    
    parser.add_argument('--rsi-oversold', '-ro',
                       default=30, type=int,
                       help='RSI oversold threshold')
    
    parser.add_argument('--rsi-overbought', '-rob',
                       default=70, type=int,
                       help='RSI overbought threshold')
    
    # Exit parameters
    parser.add_argument('--exit-middle', '-em',
                       action='store_true',
                       help='Exit when price crosses the middle band')
    
    parser.add_argument('--use-stop', '-us',
                       action='store_true',
                       help='Use stop loss')
    
    parser.add_argument('--stop-pct', '-sp',
                       default=2.0, type=float,
                       help='Stop loss percentage')
    
    parser.add_argument('--use-trail', '-ut',
                       action='store_true',
                       help='Enable trailing stop loss')
    
    parser.add_argument('--trail-pct', '-tp',
                       default=2.0, type=float,
                       help='Trailing stop percentage')
    
    # Position sizing parameters
    parser.add_argument('--risk-percent', '-riskp',
                       default=1.0, type=float,
                       help='Percentage of equity to risk per trade')
    
    parser.add_argument('--max-position', '-mp',
                       default=20.0, type=float,
                       help='Maximum position size as percentage of equity')
    
    # Trade throttling
    parser.add_argument('--trade-throttle-days', '-ttd',
                       default=1, type=int,
                       help='Minimum days between trades')
    
    # Plotting
    parser.add_argument('--plot', '-p',
                       action='store_true',
                       help='Generate and show a plot of the trading activity')
    
    return parser.parse_args()


def main():
    """Main function to run the strategy backtest"""
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
    
    # Add the Bollinger Mean Reversion strategy
    cerebro.addstrategy(
        BollingerMeanReversionStrategy,
        # Bollinger Bands parameters
        bb_length=args.bb_length,
        bb_mult=args.bb_mult,
        ma_type=args.matype,
        
        # RSI parameters
        rsi_period=args.rsi_period,
        rsi_oversold=args.rsi_oversold,
        rsi_overbought=args.rsi_overbought,
        
        # Exit parameters
        exit_middle=args.exit_middle,
        use_stop=args.use_stop,
        stop_pct=args.stop_pct,
        use_trail=args.use_trail,
        trail_pct=args.trail_pct,
        
        # Position sizing parameters
        risk_percent=args.risk_percent,
        max_position=args.max_position,
        
        # Trade throttling
        trade_throttle_days=args.trade_throttle_days,
        
        # Logging
        log_level='info'
    )
    
    # Set our desired cash start
    cerebro.broker.setcash(args.cash)
    
    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    
    # Set slippage to 0 (as required)
    cerebro.broker.set_slippage_perc(0.0)
    
    # Add standard analyzers with names expected by print_performance_metrics
    add_standard_analyzers(cerebro)
    
    # Print out the starting conditions
    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')
    
    # Print strategy configuration
    print('\nStrategy Configuration:')
    print(f'Symbol: {args.data}')
    print(f'Date Range: {args.fromdate} to {args.todate}')
    print(f'Bollinger Bands: Period={args.bb_length}, Mult={args.bb_mult}, Type={args.matype}')
    print(f'RSI: Period={args.rsi_period}, Oversold={args.rsi_oversold}, Overbought={args.rsi_overbought}')
    
    print('\nExit Parameters:')
    if args.exit_middle:
        print('Exit on middle band crossing: Enabled')
    else:
        print('Exit on middle band crossing: Disabled')
    
    if args.use_stop:
        print(f'Stop Loss: {args.stop_pct}%')
    else:
        print('Stop Loss: Disabled')
    
    if args.use_trail:
        print(f'Trailing Stop: {args.trail_pct}%')
    else:
        print('Trailing Stop: Disabled')
    
    print(f'\nPosition Sizing: {args.risk_percent}% risk per trade (max {args.max_position}%)')
    
    if args.trade_throttle_days > 0:
        print(f'Trade Throttling: {args.trade_throttle_days} days between trades')
    
    print('\n--- Starting Backtest ---\n')
    print('*** IMPORTANT: This strategy is specifically designed for SIDEWAYS/RANGING MARKETS ***')
    print('It performs poorly in trending markets where prices can remain in extreme')
    print('territories for extended periods. Best used in markets with clear trading ranges')
    print('where price regularly oscillates between support and resistance levels.\n')
    
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
