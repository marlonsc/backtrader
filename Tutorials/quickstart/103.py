# -*- coding: UTF-8 -*-
# https://www.backtrader.com/docu/quickstart/quickstart/#adding-a-data-feed

# import
import datetime  # For datetime objects
from pathlib import Path

import backtrader as bt

# globals

# functions
# Create a Strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        """
        Logging function for this strategy
        """
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] data series
        self.dataclose = self.datas[0].close

    def next(self):
        # Log the closing price of the series from the reference
        self.log(f'Close {self.dataclose[0]:,.2f}')

        # Check if there is are three day close decrease
        if self.dataclose[0] < self.dataclose[-1] < self.dataclose[-2]:
            # BUY, BUY, BUY!!! (with all possible default parameters)
            self.log(f'\tBUY CREATE {self.dataclose[0]:,.2f}')
            self.buy()

    def next_simple(self):
        # Simply log the closing price of the series from the reference
        # Index [0] is the most recent price
        # Index [-1] is the previous price
        # Index [-2] is the price before the previous price
        self.log(txt=f'Close, {self.dataclose[0]:,.2f}' )


if __name__ == '__main__':
    # Datas are in a subfolder of the samples.
    datapath = Path.cwd().parent / 'datas/orcl-1995-2014.txt'

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            # Do not pass values before this date
            fromdate=datetime.datetime(2000, 1, 1),
            # Do not pass values after this date
            todate=datetime.datetime(2000, 12, 31),
            reverse=False
    )

    cerebro = bt.Cerebro()

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100_000)

    cerebro.addstrategy(TestStrategy)

    # Print out the starting conditions
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():,.2f}')

    # Run over everything
    cerebro.run()

    # Print out the final result
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():,.2f}')
