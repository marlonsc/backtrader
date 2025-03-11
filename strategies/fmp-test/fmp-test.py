#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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

# python fmp-test.py --data TSLA --fromdate 2025-01-01 --todate 2025-03-01 --sma --period 20 --plot

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import pandas as pd
import requests
import io
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
    
    print(f"Fetching data from: {url}")
    
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
    
    print(f"Successfully fetched data for {symbol}. Shape: {df.shape}")
    return df


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=True)  # Enable standard statistics

    # Add a strategy
    cerebro.addstrategy(bt.Strategy)

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    try:
        # Get data from FMP API
        df = get_fmp_data(
            symbol=args.data,
            apikey=args.apikey,
            fromdate=fromdate,
            todate=todate
        )
        
        # Create data feed
        data = FMPData(dataname=df)
        
        # Add the data to cerebro
        cerebro.adddata(data)
        
        # Add a simple moving average if requested
        if args.sma:
            cerebro.addindicator(btind.SMA, period=args.period)
        
        # Add a writer with CSV
        if args.writer:
            cerebro.addwriter(bt.WriterFile, csv=args.wrcsv)
        
        # Run over everything
        print("Running strategy...")
        cerebro.run()
        
        # Plot if requested
        if args.plot:
            print("Plotting results...")
            cerebro.plot(style='candle', numfigs=args.numfigs, volume=True, barup='green', bardown='red')
            
    except Exception as e:
        print(f"Error: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Financial Modeling Prep Data Test')

    parser.add_argument('--data', '-d',
                        default='AAPL',
                        help='Ticker to download from FMP')

    parser.add_argument('--apikey', '-k',
                        default='849f3a33e72d49dfe694d6eda459012d',
                        help='Financial Modeling Prep API Key')

    parser.add_argument('--fromdate', '-f',
                        default='2023-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',
                        default='2023-12-31',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--period', default=20, type=int,
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--sma', action='store_true',
                        help='Add a Simple Moving Average indicator')

    parser.add_argument('--writer', '-w', action='store_true',
                        help='Add a writer to cerebro')

    parser.add_argument('--wrcsv', '-wc', action='store_true',
                        help='Enable CSV Output in the writer')

    parser.add_argument('--plot', '-p', action='store_true',
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1, type=int,
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    print("Financial Modeling Prep API Test Starting...")
    runstrat() 