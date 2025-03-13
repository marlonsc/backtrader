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
BOLLINGER BANDS MEAN REVERSION STRATEGY WITH MYSQL DATABASE - (bb_mean_reversal)
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
- Best used in SIDEWAYS or RANGE-BOUND markets
- Avoids trending markets where mean reversion is less reliable
- Performs well in consolidation periods with clear support and resistance

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
python strategies/sideways/bb_mean_reversal.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2024-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2024-12-31)

OPTIONAL ARGUMENTS:
------------------
--dbuser, -u    : MySQL username (default: root)
--dbpass, -pw   : MySQL password (default: fsck)
--dbname, -n    : MySQL database name (default: price_db)
--cash, -c      : Initial cash for the strategy (default: $100,000)
--bb_length, -bl: Period for Bollinger Bands calculation (default: 20)
--bb_mult, -bm  : Multiplier for standard deviation (default: 2.0)
--rsi_period, -rp: Period for RSI calculation (default: 14)
--rsi_oversold, -ro: RSI oversold threshold (default: 30)
--rsi_overbought, -rob: RSI overbought threshold (default: 70)
--exit_middle, -em: Exit when price crosses the middle band (default: False)
--use_stop, -us : Use stop loss (default: False) 
--stop_pct, -sp : Stop loss percentage (default: 2.0)
--matype, -mt   : Moving average type for Bollinger Bands basis (default: SMA, options: SMA, EMA, WMA, SMMA)
--plot, -p      : Generate and show a plot of the trading activity

EXAMPLE:
--------
python strategies/sideways/bb_mean_reversal.py --data AAPL --fromdate 2023-01-01 --todate 2023-12-31 --exit_middle True --use_stop True --stop_pct 2.5 --plot
"""

from __future__ import (absolute_import, division, print_function,
                       unicode_literals)

import argparse
import datetime
import os
import sys
import subprocess
import pandas as pd
import numpy as np
import mysql.connector
import matplotlib.pyplot as plt
import backtrader as bt
import backtrader.indicators as btind

# Add the parent directory to the Python path to import shared modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


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


def sync_symbol_data(symbol):
    """
    Run the sync-trade-data.sh script to update data for a specific symbol
    """
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils/sync-trade-data.sh')
    
    # Make sure the script exists and is executable
    if not os.path.isfile(script_path):
        raise Exception(f"Could not find sync script at {script_path}")
    
    if not os.access(script_path, os.X_OK):
        os.chmod(script_path, 0o755)  # Make executable if not already
    
    print(f"Syncing data for {symbol} using {script_path}")
    
    try:
        # Run the sync script with the symbol
        process = subprocess.run([script_path, symbol], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               universal_newlines=True,
                               check=True)
        
        print(f"Sync completed for {symbol}:")
        for line in process.stdout.splitlines():
            if "ADDED:" in line or "SKIPPED:" in line or "Retrieved" in line:
                print(f"  {line.strip()}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error syncing data for {symbol}: {e}")
        print(f"Error output: {e.stderr}")
        return False


def get_db_data(symbol, dbuser, dbpass, dbname, fromdate, todate):
    """
    Get historical price data from MySQL database
    """
    # Format dates for database query
    from_str = fromdate.strftime('%Y-%m-%d %H:%M:%S')
    to_str = todate.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Fetching data from MySQL database for {symbol} from {from_str} to {to_str}")
    
    # Create a directory to store sync marker files if it doesn't exist
    marker_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.sync_markers')
    if not os.path.exists(marker_dir):
        os.makedirs(marker_dir)
    
    # Path to the marker file for this symbol
    marker_file = os.path.join(marker_dir, f"{symbol.lower()}_last_sync.txt")
    
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(
            host="localhost",
            user=dbuser,
            password=dbpass,
            database=dbname
        )
        
        # Create a cursor to execute queries
        cursor = connection.cursor()
        
        # First, check if the symbol exists in the database
        check_query = """
        SELECT COUNT(*) as count
        FROM stock_prices
        WHERE symbol = %s
        """
        
        # Execute the query
        cursor.execute(check_query, (symbol,))
        result = cursor.fetchone()
        
        need_sync = False
        if not result or result[0] == 0:
            # Symbol doesn't exist in the database
            print(f"Symbol {symbol} not found in database, will sync data")
            need_sync = True
        else:
            # Check when this symbol was last synced
            last_sync_time = None
            if os.path.exists(marker_file):
                with open(marker_file, 'r') as f:
                    try:
                        last_sync_time = datetime.datetime.strptime(f.read().strip(), '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # If the timestamp is invalid, consider it as not synced
                        last_sync_time = None
            
            # If never synced or synced more than 1 hour ago, sync again
            if last_sync_time is None:
                print(f"No record of previous sync for {symbol}, will sync data")
                need_sync = True
            else:
                time_diff = datetime.datetime.now() - last_sync_time
                hours_since_sync = time_diff.total_seconds() / 3600
                
                if hours_since_sync > 1:  # 1 hour threshold
                    print(f"Data for {symbol} was last synced {hours_since_sync:.2f} hours ago, will sync new data")
                    need_sync = True
                else:
                    print(f"Data for {symbol} is up to date (last synced {time_diff.total_seconds() / 60:.1f} minutes ago)")
        
        # If we need to sync data, do it now
        if need_sync:
            if sync_symbol_data(symbol):
                # Update the marker file with current timestamp
                with open(marker_file, 'w') as f:
                    f.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Now proceed with the original query to get the data
        query = """
        SELECT date, open, high, low, close, volume
        FROM stock_prices
        WHERE symbol = %s AND date BETWEEN %s AND %s
        ORDER BY date ASC
        """
        
        # Execute the query
        cursor.execute(query, (symbol, from_str, to_str))
        
        # Fetch all results
        rows = cursor.fetchall()
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        # Check if any data was retrieved
        if not rows:
            raise Exception(f"No data found for {symbol} in the specified date range")
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        
        # Convert 'Date' to datetime and set as index
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        
        # Ensure numeric data types
        df['Open'] = pd.to_numeric(df['Open'])
        df['High'] = pd.to_numeric(df['High'])
        df['Low'] = pd.to_numeric(df['Low'])
        df['Close'] = pd.to_numeric(df['Close'])
        df['Volume'] = pd.to_numeric(df['Volume'])
        
        print(f"Successfully fetched data for {symbol}. Retrieved {len(df)} bars.")
        return df
        
    except mysql.connector.Error as err:
        raise Exception(f"Database error: {err}")
    except Exception as e:
        raise Exception(f"Error fetching data: {e}")


class BollingerMeanReversionStrategy(bt.Strategy):
    """
    Bollinger Bands Mean Reversion Strategy

    This strategy attempts to capture mean reversion moves by:
    1. Buying when price touches or crosses below the lower Bollinger Band and RSI < 30
    2. Selling when price touches or crosses above the upper Bollinger Band and RSI > 70
    
    Additional exit mechanisms include:
    - Optional exit when price crosses the middle Bollinger Band
    - Optional stop loss to limit potential losses
    """

    params = (
        ('position_size', 0.2),  # Percentage of portfolio to use per position
        ('bbands_period', 20),    # Bollinger Bands period
        ('bbands_dev', 2),        # Number of standard deviations
        ('rsi_period', 14),       # RSI period
        ('rsi_buy_threshold', 30),    # RSI threshold for buy signals
        ('rsi_sell_threshold', 70),   # RSI threshold for sell signals
        ('stop_loss_pct', 0.02),      # Stop loss percentage
        ('use_stop_loss', True),       # Whether to use stop loss
        ('exit_middle', False),        # Whether to exit when price crosses middle band
        ('log_level', 'info'),         # Logging level
    )

    def log(self, txt, dt=None, level='info'):
        """
        Logging function for the strategy
        """
        if level == 'debug' and self.params.log_level != 'debug':
            return
            
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')

    def __init__(self):
        # Store the close price reference
        self.dataclose = self.datas[0].close
        
        # Track order and position state
        self.order = None
        self.entry_price = None
        self.stop_price = None
        self.buysell = None  # 'buy' or 'sell' to track position type
        
        # Initialize trade tracking
        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # Calculate indicators
        # Bollinger Bands
        self.bbands = bt.indicators.BollingerBands(
            self.datas[0], 
            period=self.params.bbands_period,
            devfactor=self.params.bbands_dev
        )
        
        # Extract individual Bollinger Band components
        self.upper_band = self.bbands.top
        self.middle_band = self.bbands.mid
        self.lower_band = self.bbands.bot
        
        # RSI indicator
        self.rsi = bt.indicators.RSI(
            self.datas[0],
            period=self.params.rsi_period
        )
        
        # Crossover indicators for entry and exit conditions
        self.price_cross_lower = bt.indicators.CrossDown(self.dataclose, self.lower_band)
        self.price_cross_upper = bt.indicators.CrossUp(self.dataclose, self.upper_band)
        self.price_cross_middle = bt.indicators.CrossUp(self.dataclose, self.middle_band)

    def calculate_position_size(self, price, value):
        """Calculate how many shares to buy based on position sizing rules"""
        available_cash = self.broker.get_cash()
        current_price = price
        
        # Fixed percentage of available equity
        cash_to_use = value * self.params.position_size
        
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
            
        # Calculate Bollinger Band percentage (simpler approach)
        # 1.0 = at upper band, 0.5 = at middle band, 0.0 = at lower band
        bb_range = self.upper_band[0] - self.lower_band[0]
        if bb_range != 0:  # Avoid division by zero
            bb_pct = (self.dataclose[0] - self.lower_band[0]) / bb_range
        else:
            bb_pct = 0.5  # Middle band position if bands are identical (rare)
            
        # Print debug information every 10 bars
        if len(self) % 10 == 0:
            self.log(f"DEBUG - Close: {self.dataclose[0]:.2f}, BB Upper: {self.upper_band[0]:.2f}, " +
                    f"BB Middle: {self.middle_band[0]:.2f}, BB Lower: {self.lower_band[0]:.2f}, " +
                    f"RSI: {self.rsi[0]:.2f}, BB%: {bb_pct:.2f}")
            
            # Check if we're near entry conditions
            if bb_pct <= 0.2:
                self.log(f"CLOSE TO ENTRY - Price near lower band (BB%: {bb_pct:.2f}), RSI: {self.rsi[0]:.2f}")
            
            # Check if we're near exit conditions
            if bb_pct >= 0.8:
                self.log(f"CLOSE TO EXIT - Price near upper band (BB%: {bb_pct:.2f}), RSI: {self.rsi[0]:.2f}")
            
        # Log current market conditions
        self.log(f"Close: {self.dataclose[0]:.2f}, BB Upper: {self.upper_band[0]:.2f}, " +
                 f"BB Middle: {self.middle_band[0]:.2f}, BB Lower: {self.lower_band[0]:.2f}, " +
                 f"RSI: {self.rsi[0]:.2f}, BB%: {bb_pct:.2f}", level='debug')
        
        # Check for stop loss if we have a position and stop loss is enabled
        if self.position and self.params.use_stop_loss and self.stop_price is not None:
            if (self.buysell == 'buy' and self.dataclose[0] < self.stop_price) or \
               (self.buysell == 'sell' and self.dataclose[0] > self.stop_price):
                self.log(f'STOP LOSS TRIGGERED: Close Price: {self.dataclose[0]:.2f}, Stop Price: {self.stop_price:.2f}')
                self.order = self.close()
                return
                
        # Check for exit on middle band cross if enabled
        if self.position and self.params.exit_middle:
            if (self.buysell == 'buy' and self.price_cross_middle[0]) or \
               (self.buysell == 'sell' and self.price_cross_middle[0]):
                self.log(f'EXIT ON MIDDLE BAND: Close Price: {self.dataclose[0]:.2f}, Middle Band: {self.middle_band[0]:.2f}')
                self.order = self.close()
                return
        
        # If we are in a position, check for exit conditions
        if self.position:
            # For long positions, exit when price touches or crosses upper band and RSI > threshold
            if self.buysell == 'buy' and bb_pct >= 0.8 and self.rsi[0] > self.params.rsi_sell_threshold:
                self.log(f'SELL SIGNAL: Close Price: {self.dataclose[0]:.2f}, Upper Band: {self.upper_band[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.close()
        
        # If we don't have a position, check for entry conditions
        else:
            # Buy when price is near lower band and RSI is relatively low
            if bb_pct <= 0.2 and self.rsi[0] < self.params.rsi_buy_threshold:
                # Calculate position size based on current portfolio value
                price = self.dataclose[0]
                cash = self.broker.getcash()
                value = self.broker.getvalue()
                size = self.calculate_position_size(price, value)
                
                self.log(f'BUY SIGNAL: Close Price: {price:.2f}, Lower Band: {self.lower_band[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                self.log(f'ORDER DETAILS: Size: {size}, Price: {price:.2f}, Value: {value:.2f}, Cash: {cash:.2f}')
                
                # Keep track of the executed price
                self.entry_price = price
                
                # Set stop price if using stop loss
                if self.params.use_stop_loss:
                    self.stop_price = price * (1.0 - self.params.stop_loss_pct)
                    self.log(f'Stop price set at {self.stop_price:.2f} ({self.params.stop_loss_pct*100:.1f}% below entry)')
                
                # Enter long position
                self.buysell = 'buy'
                self.order = self.buy(size=size)

    def stop(self):
        """Called when backtest is finished"""
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}')
        
        # Calculate and log statistics
        if self.trade_count > 0:
            win_rate = (self.winning_trades / self.trade_count) * 100
            self.log(f'Trade Statistics: {self.trade_count} trades, {win_rate:.2f}% win rate')
        else:
            self.log('No trades executed during the backtest period')

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
        description='Bollinger Bands Mean Reversion Strategy with RSI (for Sideways Markets)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # Basic input parameters
    parser.add_argument('--data', '-d',
                        default='AAPL',
                        help='Stock symbol to retrieve data for')
    
    parser.add_argument('--dbuser', '-u',
                        default='root',
                        help='MySQL username')
    
    parser.add_argument('--dbpass', '-pw',
                        default='fsck',
                        help='MySQL password')
    
    parser.add_argument('--dbname', '-n',
                        default='price_db',
                        help='MySQL database name')
    
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
    parser.add_argument('--bb_length', '-bl',
                        default=20, type=int,
                        help='Period for Bollinger Bands calculation')
    
    parser.add_argument('--bb_mult', '-bm',
                        default=2.0, type=float,
                        help='Multiplier for standard deviation')
    
    parser.add_argument('--matype', '-mt',
                        default='SMA',
                        choices=['SMA', 'EMA', 'WMA', 'SMMA'],
                        help='Moving average type for Bollinger Bands basis')
    
    # RSI parameters
    parser.add_argument('--rsi_period', '-rp',
                        default=14, type=int,
                        help='Period for RSI calculation')
    
    parser.add_argument('--rsi_oversold', '-ro',
                        default=30, type=int,
                        help='RSI oversold threshold (buy signal)')
    
    parser.add_argument('--rsi_overbought', '-rob',
                        default=70, type=int,
                        help='RSI overbought threshold (sell signal)')
    
    # Exit strategy parameters
    parser.add_argument('--exit_middle', '-em',
                        action='store_true',
                        help='Exit when price crosses the middle band')
    
    parser.add_argument('--use_stop', '-us',
                        action='store_true',
                        help='Use stop loss')
    
    parser.add_argument('--stop_pct', '-sp',
                        default=2.0, type=float,
                        help='Stop loss percentage from entry')
    
    # Position sizing parameters
    parser.add_argument('--position_percent', '-pp',
                        default=20.0, type=float,
                        help='Percentage of equity to use per trade')
    
    parser.add_argument('--max_position_percent', '-mpp',
                        default=95.0, type=float,
                        help='Maximum percentage of equity to use per trade')
    
    # Plotting
    parser.add_argument('--plot', '-p', action='store_true',
                        help='Generate and show a plot of the trading activity')
    
    return parser.parse_args()


def main():
    """
    Main function to run the strategy
    """
    args = parse_args()
    
    # Convert dates
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
    
    # Fetch data from MySQL database
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
        bbands_period=args.bb_length,
        bbands_dev=args.bb_mult,
        rsi_period=args.rsi_period,
        rsi_buy_threshold=args.rsi_oversold,
        rsi_sell_threshold=args.rsi_overbought,
        stop_loss_pct=args.stop_pct / 100,  # Convert percentage to decimal
        use_stop_loss=args.use_stop,
        exit_middle=args.exit_middle,
        position_size=args.position_percent  # Change position_percent to position_size
    )
    
    # Set our desired cash start
    cerebro.broker.setcash(args.cash)
    
    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    
    # Set slippage to 0 (as required)
    cerebro.broker.set_slippage_perc(0.0)
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Print strategy configuration
    print('\nStrategy Configuration:')
    print(f'- Data Source: MySQL database ({args.dbname})')
    print(f'- Symbol: {args.data}')
    print(f'- Date Range: {args.fromdate} to {args.todate}')
    print(f'- Entry: Price below lower BB AND RSI < {args.rsi_oversold}')
    print(f'- Exit: Price above upper BB AND RSI > {args.rsi_overbought}')
    
    if args.exit_middle:
        print(f'- Additional Exit: Price crosses above middle band')
    
    if args.use_stop:
        print(f'- Stop Loss: {args.stop_pct}% below entry price')
    
    print(f'- Position Sizing: Using {args.position_percent}% of equity per trade')
    
    print('\n--- Starting Backtest ---\n')
    
    # Run the strategy
    results = cerebro.run()
    strat = results[0]
    
    # Print out final results
    print('\n--- Backtest Results ---\n')
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Get analyzer results
    try:
        returns = strat.analyzers.returns.get_analysis()
        total_return = returns.get('rtot', 0) * 100
        print(f'Return: {total_return:.2f}%')
    except Exception as e:
        print('Unable to calculate return')
    
    try:
        sharpe = strat.analyzers.sharperatio.get_analysis()
        sharpe_ratio = sharpe.get('sharperatio', 0)
        print(f'Sharpe Ratio: {sharpe_ratio:.4f}')
    except Exception as e:
        print('Unable to calculate Sharpe ratio')
    
    try:
        drawdown = strat.analyzers.drawdown.get_analysis()
        max_dd = drawdown.get('max', {}).get('drawdown', 0)
        print(f'Max Drawdown: {max_dd:.2f}%')
    except Exception as e:
        print('Unable to calculate Max Drawdown')
    
    try:
        trades = strat.analyzers.trades.get_analysis()
        total_trades = trades.get('total', {}).get('total', 0)
        won_trades = trades.get('won', {}).get('total', 0)
        lost_trades = trades.get('lost', {}).get('total', 0)
        win_rate = won_trades / total_trades * 100 if total_trades > 0 else 0
        print(f'Total Trades: {total_trades}')
        print(f'Won Trades: {won_trades}')
        print(f'Lost Trades: {lost_trades}')
        print(f'Win Rate: {win_rate:.2f}%')
    except Exception as e:
        print('Unable to calculate trade statistics')
    
    # Plot if requested
    if args.plot:
        cerebro.plot(style='candle', barup='green', bardown='red', 
                    volup='green', voldown='red', 
                    fill_up='green', fill_down='red',
                    plotdist=0.5, width=16, height=9)


if __name__ == '__main__':
    main()
