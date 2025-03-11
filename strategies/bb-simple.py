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
BOLLINGER BANDS TRADING STRATEGY WITH FINANCIAL MODELING PREP API
=================================================================

This script implements a trading strategy that uses Bollinger Bands to generate
buy and sell signals. The strategy is based on price breakthroughs of the bands:

STRATEGY LOGIC:
--------------
- Go LONG when price closes ABOVE the UPPER Bollinger Band
- Exit LONG (go flat) when price closes BELOW the LOWER Bollinger Band
- No short positions are taken

BOLLINGER BANDS:
--------------
Bollinger Bands consist of:
- A middle band (typically a 20-period moving average)
- An upper band (middle band + 2 standard deviations)
- A lower band (middle band - 2 standard deviations)

These bands adapt to volatility - widening during volatile periods and 
narrowing during less volatile periods.

USAGE:
------
python strategies/bb-simple.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2024-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2024-12-31)

OPTIONAL ARGUMENTS:
------------------
--apikey, -k    : Your FMP API key (default is provided but can be changed)
--cash, -c      : Initial cash for the strategy (default: $100,000)
--length, -l    : Period for Bollinger Bands calculation (default: 20)
--mult, -m      : Multiplier for standard deviation (default: 2.0)
--matype, -mt   : Moving average type for basis (default: SMA, options: SMA, EMA, WMA, SMMA)
--plot, -p      : Generate and show a plot of the trading activity

EXAMPLE:
--------
python strategies/bb-simple.py --data AAPL --fromdate 2023-01-01 --todate 2023-12-31 --length 20 --mult 2.0 --matype SMA --plot
"""

from __future__ import (absolute_import, division, print_function,
                       unicode_literals)

import argparse
import datetime
import pandas as pd
import requests
import io
import matplotlib.pyplot as plt
import backtrader as bt
import backtrader.indicators as btind


class FMPData(bt.feeds.PandasData):
    """
    Financial Modeling Prep Data Feed
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


def get_fmp_data(symbol, apikey, fromdate, todate):
    """
    Get historical price data from Financial Modeling Prep API
    """
    # Format dates for API request
    from_str = fromdate.strftime('%Y-%m-%d')
    to_str = todate.strftime('%Y-%m-%d')
    
    # Build URL
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
    url += f"?from={from_str}&to={to_str}&apikey={apikey}"
    
    print(f"Fetching data from FMP API for {symbol} from {from_str} to {to_str}")
    
    # Make request
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
    
    data = response.json()
    
    if 'historical' not in data:
        raise Exception(f"No historical data returned for {symbol}")
    
    # Convert to pandas DataFrame
    historical_data = data['historical']
    df = pd.DataFrame(historical_data)
    
    # Rename columns to match backtrader's expected format
    df = df.rename(columns={
        'date': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    # Set the date as index and sort from oldest to newest
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    df = df.sort_index()
    
    # Select only the columns we need
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    print(f"Successfully fetched data for {symbol}. Retrieved {len(df)} bars.")
    return df


class BollingerBandsStrategy(bt.Strategy):
    """
    Strategy that implements the Bollinger Bands trading rules:
    - Go long when price closes above the upper Bollinger Band
    - Multiple exit strategies available (see below)
    - Only trades within the specified date range
    
    Exit Strategy Options:
    - 'lower_band': Exit when price closes below the lower Bollinger Band
    - 'middle_band': Exit when price closes below the middle Bollinger Band (default)
    - 'bars': Exit after a specified number of bars
    - 'trailing_percent': Exit using a trailing stop based on percentage
    - 'trailing_atr': Exit using a trailing stop based on ATR
    - 'trailing_ma': Exit when price crosses below a moving average
    
    Position Sizing Options:
    - 'percent': Use a fixed percentage of available equity (default 20%)
    - 'auto': Size based on volatility (less volatile = larger position)
    
    Additional Features:
    - Trade throttling to limit trade frequency
    - Risk management with stop loss functionality
    """
    params = (
        ('length', 20),          # Period for Bollinger Bands calculation
        ('mult', 2.0),           # Multiplier for standard deviation
        ('matype', 'SMA'),       # MA type for basis
        ('startdate', None),     # Start date for trading
        ('enddate', None),       # End date for trading
        ('printlog', False),     # Print log for each trade
        
        # Exit strategy parameters
        ('exit_strategy', 'middle_band'),  # Exit strategy: 'lower_band', 'middle_band', 'bars', 'trailing_percent', 'trailing_atr', 'trailing_ma'
        ('exit_bars', 5),        # Number of bars to hold position when exit_strategy='bars'
        ('trailing_percent', 2.0), # Percentage for trailing stop when exit_strategy='trailing_percent'
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
        
        # Create the appropriate moving average type
        if self.p.matype == 'SMA':
            ma_class = bt.indicators.SimpleMovingAverage
        elif self.p.matype == 'EMA':
            ma_class = bt.indicators.ExponentialMovingAverage
        elif self.p.matype == 'WMA':
            ma_class = bt.indicators.WeightedMovingAverage
        elif self.p.matype == 'SMMA' or self.p.matype == 'SMMA (RMA)':
            ma_class = bt.indicators.SmoothedMovingAverage
        else:
            # Default to SMA
            ma_class = bt.indicators.SimpleMovingAverage
        
        # Create Bollinger Bands indicator
        self.bband = bt.indicators.BollingerBands(
            self.dataclose, 
            period=self.p.length,
            devfactor=self.p.mult,
            movav=ma_class,
            plot=True,
            plotname='Bollinger Bands'
        )
        
        # Additional indicators based on exit strategies
        
        # ATR for trailing stop
        if self.p.exit_strategy == 'trailing_atr':
            self.atr = bt.indicators.ATR(self.data, period=self.p.trailing_atr_period)
        
        # Moving Average for trailing MA stop
        if self.p.exit_strategy == 'trailing_ma':
            self.trailing_ma = ma_class(self.dataclose, period=self.p.trailing_ma_period)
        
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

            # Record the size of the bar where the trade was executed
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
        # Basic exit strategies based on price crossings
        if self.p.exit_strategy == 'lower_band':
            return self.dataclose[0] < self.bband.bot[0]
            
        elif self.p.exit_strategy == 'middle_band':
            return self.dataclose[0] < self.bband.mid[0]
            
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
                    f'BB Top: {self.bband.top[0]:.2f}, '
                    f'BB Mid: {self.bband.mid[0]:.2f}, '
                    f'BB Bot: {self.bband.bot[0]:.2f}', doprint=True)
                    
            # Show trailing stop info if in a position
            if self.position and hasattr(self, 'trailing_stop_price') and self.trailing_stop_price > 0:
                self.log(f'Trailing Stop: {self.trailing_stop_price:.2f}', doprint=True)

        # Check if we are in the market
        if not self.position:
            # Long condition: Price closes above upper band
            if self.dataclose[0] > self.bband.top[0]:
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
                # For debug: Check why we're not entering
                if self.dataclose[0] > self.bband.mid[0]:
                    self.log('Price above mid band but not above upper band', doprint=True)
        else:
            # We are in a position, check if we should exit
            if self.should_exit_trade():
                reason = ''
                # Add reason for exit to log
                if self.p.exit_strategy == 'lower_band':
                    reason = 'Price below lower band'
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
            else:
                # For debug: Check our position status
                if self.dataclose[0] < self.bband.mid[0]:
                    self.log('Price below mid band but not triggering exit', doprint=True)

    def stop(self):
        # Log final results when strategy is complete
        self.log('Final Portfolio Value: %.2f' % self.broker.getvalue(), doprint=True)
        

def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Enhanced Bollinger Bands Strategy with data from Financial Modeling Prep API',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # Basic input parameters
    parser.add_argument('--data', '-d',
                        default='AAPL',
                        help='Ticker to download from FMP')
    
    parser.add_argument('--apikey', '-k',
                        default='849f3a33e72d49dfe694d6eda459012d',
                        help='Financial Modeling Prep API Key')
    
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
    parser.add_argument('--length', '-l',
                        default=20, type=int,
                        help='Period for Bollinger Bands calculation')
    
    parser.add_argument('--mult', '-m',
                        default=2.0, type=float,
                        help='Multiplier for standard deviation')
    
    parser.add_argument('--matype', '-mt',
                        default='SMA',
                        choices=['SMA', 'EMA', 'WMA', 'SMMA'],
                        help='Moving average type for basis')
    
    # Exit strategy parameters
    parser.add_argument('--exit_strategy', '-es',
                        default='middle_band',
                        choices=['lower_band', 'middle_band', 'bars', 'trailing_percent', 'trailing_atr', 'trailing_ma'],
                        help='Exit strategy to use')
    
    parser.add_argument('--exit_bars', '-eb',
                        default=5, type=int,
                        help='Number of bars to hold position when exit_strategy=bars')
    
    parser.add_argument('--trailing_percent', '-tp',
                        default=2.0, type=float,
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
    """
    Main function
    """
    args = parse_args()
    
    # Convert dates
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
    
    # Fetch data from FMP API
    try:
        df = get_fmp_data(args.data, args.apikey, fromdate, todate)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
    
    # Create data feed
    data = FMPData(dataname=df)
    
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Add the data feed to cerebro
    cerebro.adddata(data)
    
    # Add strategy with all the enhanced parameters
    cerebro.addstrategy(
        BollingerBandsStrategy,
        # Bollinger Bands parameters
        length=args.length,
        mult=args.mult,
        matype=args.matype,
        startdate=fromdate,
        enddate=todate,
        printlog=True,
        
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
    print(f'- Entry: Price closes above upper Bollinger Band')
    print(f'- Exit Strategy: {args.exit_strategy}')
    
    if args.exit_strategy == 'bars':
        print(f'  (Exit after {args.exit_bars} bars)')
    elif args.exit_strategy == 'trailing_percent':
        print(f'  (Using {args.trailing_percent}% trailing stop)')
    elif args.exit_strategy == 'trailing_atr':
        print(f'  (Using {args.trailing_atr_mult}x ATR({args.trailing_atr_period}) trailing stop)')
    elif args.exit_strategy == 'trailing_ma':
        print(f'  (Using {args.trailing_ma_period} period MA as trailing stop)')
    
    print(f'- Position Sizing: {args.position_sizing}')
    if args.position_sizing == 'percent':
        print(f'  (Using {args.position_percent}% of equity per trade)')
    else:
        print(f'  (Auto-sizing based on {args.risk_percent}% risk per trade)')
    
    if args.trade_throttle_hours > 0:
        print(f'- Trade Throttling: Minimum {args.trade_throttle_hours} hours between trades')
    
    if args.use_stop_loss:
        print(f'- Stop Loss: {args.stop_loss_percent}% from entry')
    
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