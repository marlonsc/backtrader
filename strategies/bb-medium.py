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
GAUSSIAN CHANNEL STRATEGY WITH STOCHASTIC RSI AND BOLLINGER BANDS
=================================================================

This script implements a more advanced trading strategy that combines:
1. Gaussian Channel indicator
2. Stochastic RSI
3. Bollinger Bands

STRATEGY LOGIC:
--------------
- Go LONG when:
  a. The gaussian channel is green (filt > filt[1])
  b. The close price is above the high gaussian channel band
  c. The Stochastic RSI is above 80 or below 20
- Exit LONG (go flat) when the close price crosses below the high gaussian channel band
- No short positions are taken

USAGE:
------
python strategies/bb-medium.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2018-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2069-12-31)

OPTIONAL ARGUMENTS:
------------------
--apikey, -k    : Your FMP API key (default is provided but can be changed)
--cash, -c      : Initial cash for the strategy (default: $100,000)
--bblength, -bl : Period for Bollinger Bands calculation (default: 20)
--bbmult, -bm   : Multiplier for Bollinger Bands standard deviation (default: 2.0)
--matype, -mt   : Moving average type for basis (default: SMA, options: SMA, EMA, WMA, SMMA)
--rsilength, -rl: Period for RSI calculation (default: 14)
--stochlength, -sl: Period for Stochastic calculation (default: 14)
--smoothk, -sk  : Smoothing K period for Stochastic RSI (default: 3)
--smoothd, -sd  : Smoothing D period for Stochastic RSI (default: 3)
--poles, -po    : Number of poles for Gaussian Filter (default: 4, range: 1-9)
--period, -pe   : Sampling period for Gaussian Filter (default: 144, min: 2)
--trmult, -tm   : Multiplier for Filtered True Range (default: 1.414)
--lag, -lg      : Enable reduced lag mode (default: False)
--fast, -fa     : Enable fast response mode (default: False)
--plot, -p      : Generate and show a plot of the trading activity

EXAMPLE:
--------
python strategies/bb-medium.py --data AAPL --fromdate 2023-01-01 --todate 2023-12-31 --plot
"""

from __future__ import (absolute_import, division, print_function,
                       unicode_literals)

import argparse
import datetime
import math
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


class StochasticRSI(bt.Indicator):
    """
    Stochastic RSI Indicator
    
    Formula:
    - RSI = Relative Strength Index
    - K = SMA(Stochastic(RSI, RSI, RSI, period), smoothK)
    - D = SMA(K, smoothD)
    
    Params:
    - rsi_length: Period for RSI calculation
    - stoch_length: Period for Stochastic calculation
    - k_smooth: Smoothing period for K line
    - d_smooth: Smoothing period for D line
    """
    lines = ('k', 'd')
    params = (
        ('rsi_length', 14),
        ('stoch_length', 14),
        ('k_smooth', 3),
        ('d_smooth', 3),
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
        self.rsi = bt.indicators.RSI(self.data, period=self.p.rsi_length)
        
        # Calculate highest and lowest RSI values over the stoch_length period
        self.highest_rsi = bt.indicators.Highest(self.rsi, period=self.p.stoch_length)
        self.lowest_rsi = bt.indicators.Lowest(self.rsi, period=self.p.stoch_length)
        
        # Calculate raw K value (not smoothed yet)
        # K = (Current RSI - Lowest RSI) / (Highest RSI - Lowest RSI) * 100
        self.rsi_diff = self.highest_rsi - self.lowest_rsi
        self.raw_k = 100.0 * (self.rsi - self.lowest_rsi) / (self.rsi_diff + 0.000001)  # Avoid division by zero
        
        # Apply smoothing to K and D lines
        self.lines.k = bt.indicators.SMA(self.raw_k, period=self.p.k_smooth)
        self.lines.d = bt.indicators.SMA(self.lines.k, period=self.p.d_smooth)


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


class GaussianChannelStrategy(bt.Strategy):
    """
    Strategy that implements the Gaussian Channel with Stochastic RSI trading rules:
    - Open long position when:
      - The gaussian channel is green (filt > filt[1])
      - The close price is above the high gaussian channel band
      - The Stochastic RSI is above 80 or below 20
    - Close long positions when the close price crosses the high gaussian channel band to the downside
    - Only trades within the specified date range
    """
    params = (
        # Bollinger Bands parameters
        ('bblength', 20),        # Period for Bollinger Bands calculation
        ('bbmult', 2.0),         # Multiplier for standard deviation
        ('bbmatype', 'SMA'),     # MA type for basis
        
        # Stochastic RSI parameters
        ('rsilength', 14),       # Period for RSI calculation
        ('stochlength', 14),     # Period for Stochastic calculation
        ('smoothk', 3),          # Smoothing K period
        ('smoothd', 3),          # Smoothing D period
        
        # Gaussian Channel parameters
        ('poles', 4),            # Number of poles (1-9)
        ('period', 144),         # Sampling period (min: 2)
        ('trmult', 1.414),       # Filtered True Range multiplier
        ('lag_reduction', False), # Reduced lag mode
        ('fast_response', False), # Fast response mode
        
        # Date range parameters
        ('startdate', datetime.datetime(2018, 1, 1)),  # Start date for trading
        ('enddate', datetime.datetime(2069, 12, 31)),  # End date for trading
        
        ('printlog', False),     # Print log for each trade
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
        
        # Create the appropriate moving average type for Bollinger Bands
        if self.p.bbmatype == 'SMA':
            ma_class = bt.indicators.SimpleMovingAverage
        elif self.p.bbmatype == 'EMA':
            ma_class = bt.indicators.ExponentialMovingAverage
        elif self.p.bbmatype == 'WMA':
            ma_class = bt.indicators.WeightedMovingAverage
        elif self.p.bbmatype == 'SMMA' or self.p.bbmatype == 'SMMA (RMA)':
            ma_class = bt.indicators.SmoothedMovingAverage
        else:
            # Default to SMA
            ma_class = bt.indicators.SimpleMovingAverage
        
        # Create Bollinger Bands indicator
        self.bband = bt.indicators.BollingerBands(
            self.dataclose, 
            period=self.p.bblength,
            devfactor=self.p.bbmult,
            movav=ma_class,
            plot=True,
            plotname='Bollinger Bands'
        )
        
        # Create Stochastic RSI indicator
        self.stoch_rsi = StochasticRSI(
            self.data,
            rsi_length=self.p.rsilength,
            stoch_length=self.p.stochlength,
            k_smooth=self.p.smoothk,
            d_smooth=self.p.smoothd
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

        # Check if we are in the market
        if not self.position:
            # LONG CONDITIONS:
            # 1. Gaussian channel is green (filt > filt[1])
            # 2. Close price is above the high gaussian channel band
            # 3. Stochastic RSI is above 80 or below 20
            is_gaussian_green = self.gaussian.filt[0] > self.gaussian.filt[-1]
            is_close_above_band = self.dataclose[0] > self.gaussian.hband[0]
            is_stoch_rsi_signal = self.stoch_rsi.k[0] > 80 or self.stoch_rsi.k[0] < 20
            
            if is_gaussian_green and is_close_above_band and is_stoch_rsi_signal:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                # Use all available cash (100% of equity)
                cash = self.broker.get_cash()
                size = int(cash / self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(size=size)
        else:
            # EXIT CONDITIONS:
            # Close price crosses the high gaussian channel band to the downside
            is_cross_below_band = self.dataclose[-1] >= self.gaussian.hband[-1] and self.dataclose[0] < self.gaussian.hband[0]
            
            if is_cross_below_band:
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
        description='Demo GPT - Gaussian Channel Strategy with Stochastic RSI and Bollinger Bands')
    
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
                        default='2069-12-31',
                        help='Ending date in YYYY-MM-DD format')
    
    parser.add_argument('--cash', '-c',
                        default=100000.0, type=float,
                        help='Starting cash')
    
    # Bollinger Bands parameters
    parser.add_argument('--bblength', '-bl',
                        default=20, type=int,
                        help='Period for Bollinger Bands calculation')
    
    parser.add_argument('--bbmult', '-bm',
                        default=2.0, type=float,
                        help='Multiplier for Bollinger Bands standard deviation')
    
    parser.add_argument('--matype', '-mt',
                        default='SMA',
                        choices=['SMA', 'EMA', 'WMA', 'SMMA'],
                        help='Moving average type for basis')
    
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
        bblength=args.bblength,
        bbmult=args.bbmult,
        bbmatype=args.matype,
        rsilength=args.rsilength,
        stochlength=args.stochlength,
        smoothk=args.smoothk,
        smoothd=args.smoothd,
        poles=args.poles,
        period=args.period,
        trmult=args.trmult,
        lag_reduction=args.lag,
        fast_response=args.fast,
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