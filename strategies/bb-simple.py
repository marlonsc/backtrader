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
    - Close long when price closes below the lower Bollinger Band
    - Only trades within the specified date range
    """
    params = (
        ('length', 20),          # Period for Bollinger Bands calculation
        ('mult', 2.0),           # Multiplier for standard deviation
        ('matype', 'SMA'),       # MA type for basis
        ('startdate', None),     # Start date for trading
        ('enddate', None),       # End date for trading
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
            # Long condition: Price closes above upper band
            if self.dataclose[0] > self.bband.top[0]:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                # Use all available cash (100% of equity)
                cash = self.broker.get_cash()
                size = int(cash / self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(size=size)
        else:
            # Exit condition: Price closes below lower band
            if self.dataclose[0] < self.bband.bot[0]:
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
        description='Bollinger Bands Strategy with data from Financial Modeling Prep API')
    
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
        BollingerBandsStrategy,
        length=args.length,
        mult=args.mult,
        matype=args.matype,
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
                    plotdist=0.5, width=16, height=9)


if __name__ == '__main__':
    main() 