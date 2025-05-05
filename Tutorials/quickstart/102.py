# -*- coding: UTF-8 -*-
# https://www.backtrader.com/docu/quickstart/quickstart/#adding-a-data-feed

# import
import datetime  # For datetime objects
from pathlib import Path

import backtrader as bt

# globals

# functions


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

    # Print out the starting conditions
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():,.2f}')

    # Run over everything
    cerebro.run()

    # Print out the final result
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():,.2f}')
