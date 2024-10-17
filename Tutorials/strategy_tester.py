# -*- coding: UTF-8 -*-
# https://www.backtrader.com/docu/quickstart/quickstart/#adding-a-data-feed

# import
from datetime import datetime  # For datetime objects
from pathlib import Path

import pandas as pd

import backtrader as bt
from test_strategies import TestStrategy_SMA


# globals
debug = False

# functions/classes




if __name__ == '__main__':
    # Datas are in a subfolder of the samples.
    ticker_data = Path.cwd().parent / 'datas/orcl-1995-2014.txt'

    # Create a Data Feed
    data_0 = bt.feeds.YahooFinanceCSVData(
            dataname=ticker_data,
            # Do not pass values before this date
            fromdate=datetime(2000, 1, 1),
            # Do not pass values after this date
            todate=datetime(2000, 12, 31),
            reverse=False
    )

    cerebro = bt.Cerebro()

    # Add the Data Feed to Cerebro
    cerebro.adddata(data_0)

    # Set our desired cash start
    cerebro.broker.setcash(100_000)

    # 105 Set the commission - 0.1% --> 0.001
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    cerebro.addstrategy(TestStrategy_SMA, bars_since_last_sell=5)   # see params in TestStrategy

    # Print out the starting conditions
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():,.2f}')

    # Run over everything
    cerebro.run()

    print('Trade Results:')

    df: pd.DataFrame = cerebro.runstrats[0][0].trade_results
    print(df)
    print(f'Profit (w/o commission):\t{df.pnl.sum():,.2f}')
    print(f'Profit (incl. commission)\t{df.pnlcomm.sum():,.2f}')

    # Print out the final result
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():,.2f}')

    if debug:    # Print out the final result
        print('#\tDate\t\tOpen\tHigh\tLow\tClose\t\tVolume\tAdj Close')
        for i in range(len(data_0)):
            x = data_0._load()
            print(
                f'{i}\t{data_0.datetime.date(0)}\t{data_0.open[0]:.2f}\t'
                f'{data_0.high[0]:.2f}\t{data_0.low[0]:.2f}\t{data_0.close[0]:.2f}\t'
                f'{data_0.volume[0]:.2f}\t{data_0.close[0]:.2f}'
                )

