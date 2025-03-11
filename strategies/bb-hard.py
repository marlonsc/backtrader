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
GAUSSIAN CHANNEL WITH STOCHASTIC RSI TRADING STRATEGY
=====================================================

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
--apikey, -k    : Your FMP API key (default is provided but can be changed)
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
python strategies/bb-hard.py --data AAPL --fromdate 2023-01-01 --todate 2023-06-30 --plot
"""

from __future__ import (absolute_import, division, print_function,
                       unicode_literals)

import argparse
import datetime
import math
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import backtrader as bt
import backtrader.indicators as btind
from backtrader.utils.py3 import range


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


class GaussianChannelStrategy(bt.Strategy):
    """
    Strategy that implements the Gaussian Channel with Stochastic RSI trading rules:
    - Open long position when:
      - Price closes above the upper Gaussian Channel line
      - Stochastic RSI K line is above D line (stochastic is "up")
    - Close long positions when the price closes below the upper Gaussian Channel line
    - Only trades within the specified date range
    """
    params = (
        # Gaussian Channel parameters
        ('gausslength', 20),    # Period for Gaussian Channel calculation (minimum 5)
        ('multiplier', 2.0),    # Multiplier for standard deviation bands
        
        # Stochastic RSI parameters
        ('rsilength', 14),      # Period for RSI calculation
        ('stochlength', 14),    # Period for Stochastic calculation
        ('klength', 3),         # Smoothing K period
        ('dlength', 3),         # Smoothing D period
        
        # Date range parameters
        ('startdate', datetime.datetime(2018, 1, 1)),  # Start date for trading
        ('enddate', datetime.datetime(2069, 1, 1)),    # End date for trading
        
        ('printlog', False),    # Print log for each trade
    )
    
    def __init__(self):
        # Keep track of close price
        self.dataclose = self.datas[0].close
        
        # To keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
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
            klength=self.p.klength,
            dlength=self.p.dlength
        )
        
        # Create Gaussian Channel indicator
        self.gaussian = GaussianChannel(
            self.data,
            length=self.p.gausslength,
            multiplier=self.p.multiplier
        )

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
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log(
                    'SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f' %
                    (order.executed.price,
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
                    f'GC Mid: {self.gaussian.mid[0]:.2f}, '
                    f'GC Upper: {self.gaussian.upper[0]:.2f}, '
                    f'GC Lower: {self.gaussian.lower[0]:.2f}, '
                    f'StochRSI K: {self.stoch_rsi.k[0]:.2f}, '
                    f'D: {self.stoch_rsi.d[0]:.2f}', doprint=True)

        # Check if we are in the market
        if not self.position:
            # LONG CONDITIONS:
            # 1. Price closes above the upper Gaussian Channel line
            # 2. Stochastic RSI K line is above D line (stochastic is "up")
            price_above_upper = self.dataclose[0] > self.gaussian.upper[0]
            stoch_rsi_up = self.stoch_rsi.k[0] > self.stoch_rsi.d[0]
            
            if price_above_upper and stoch_rsi_up:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                # Use 95% of available cash to leave buffer for commissions
                cash = self.broker.get_cash() * 0.95
                size = int(cash / self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(size=size)
            elif price_above_upper:
                self.log('Price above upper band but StochRSI not up', doprint=True)
            elif stoch_rsi_up:
                self.log('StochRSI up but price not above upper band', doprint=True)
        else:
            # EXIT CONDITIONS:
            # Price closes below the upper Gaussian Channel line
            price_below_upper = self.dataclose[0] < self.gaussian.upper[0]
            
            if price_below_upper:
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
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
        description='Gaussian Channel with Stochastic RSI Strategy')
    
    parser.add_argument('--data', '-d',
                        default='AAPL',
                        help='Ticker to download from FMP')
    
    parser.add_argument('--apikey', '-k',
                        default='849f3a33e72d49dfe694d6eda459012d',
                        help='Financial Modeling Prep API Key')
    
    parser.add_argument('--fromdate', '-f',
                        default='2018-01-01',
                        help='Starting date in YYYY-MM-DD format')
    
    parser.add_argument('--todate', '-t',
                        default='2069-01-01',
                        help='Ending date in YYYY-MM-DD format')
    
    parser.add_argument('--cash', '-c',
                        default=100000.0, type=float,
                        help='Starting cash')
    
    # Gaussian Channel parameters
    parser.add_argument('--gausslength', '-gl',
                        default=20, type=int,
                        help='Period for Gaussian Channel calculation (minimum: 5)')
    
    parser.add_argument('--multiplier', '-m',
                        default=2.0, type=float,
                        help='Multiplier for Gaussian standard deviation bands')
    
    # Stochastic RSI parameters
    parser.add_argument('--rsilength', '-rl',
                        default=14, type=int,
                        help='Period for RSI calculation')
    
    parser.add_argument('--stochlength', '-sl',
                        default=14, type=int,
                        help='Period for Stochastic calculation')
    
    parser.add_argument('--klength', '-kl',
                        default=3, type=int,
                        help='Smoothing K period for Stochastic RSI')
    
    parser.add_argument('--dlength', '-dl',
                        default=3, type=int,
                        help='Smoothing D period for Stochastic RSI')
    
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
    
    # Add strategy
    cerebro.addstrategy(
        GaussianChannelStrategy,
        gausslength=args.gausslength,
        multiplier=args.multiplier,
        rsilength=args.rsilength,
        stochlength=args.stochlength,
        klength=args.klength,
        dlength=args.dlength,
        startdate=fromdate,
        enddate=todate,
        printlog=True
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
    
    # Run the strategy
    results = cerebro.run()
    strat = results[0]
    
    # Print out final results
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
                    plotdist=0.5)


if __name__ == '__main__':
    main() 