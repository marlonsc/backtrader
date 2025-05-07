# -*- coding: UTF-8 -*-
# https://www.backtrader.com/docu/quickstart/quickstart/#adding-a-data-feed

# import
from datetime import datetime  # For datetime objects
from pathlib import Path

import backtrader as bt
import pandas as pd
from test_strategies import (
    PlayWithIndicators,
    TestStrategy_SMA,
)

# globals
debug = False

# functions/classes


if __name__ == "__main__":
    # Datas are in a subfolder of the samples.
    datas = Path.cwd() / "datas"
    ticker_data = datas / "2006-day-001.txt"  # 'datas/orcl-1995-2014.txt'
    ticker_weekly = datas / "2006-week-001.txt"

    # Create a Data Feed
    data_0 = bt.feeds.YahooFinanceCSVData(
        dataname=ticker_data,
        # Do not pass values before this date
        fromdate=datetime(2006, 1, 1),
        # Do not pass values after this date
        todate=datetime(2006, 12, 31),
        reverse=False,
        adjclose=False,
        adjvolume=False,
        timeframe=bt.TimeFrame.Days,
    )

    data_weekly = bt.feeds.YahooFinanceCSVData(
        dataname=ticker_weekly,
        # Do not pass values before this date
        fromdate=datetime(2006, 1, 1),
        # Do not pass values after this date
        todate=datetime(2006, 12, 31),
        reverse=False,
        adjclose=False,
        adjvolume=False,
        timeframe=bt.TimeFrame.Weeks,
    )

    cerebro = bt.Cerebro()

    # Add the Data Feed to Cerebro
    cerebro.adddata(data_0)
    # cerebro.adddata(data_weekly)

    # Set our desired cash start
    cerebro.broker.setcash(1_000)

    # 105 Set the commission - 0.1% --> 0.001
    cerebro.broker.setcommission(commission=0.00)
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # add one strategy with a parameter
    # cerebro.addstrategy(TestStrategy_SMA, ma_period = 17)   # see params in
    # TestStrategy

    # Try the strategy w multiple parameters
    if False:
        strats = cerebro.optstrategy(
            TestStrategy_SMA,
            ma_period=[3, 10, 15, 18, 22, 35],  # range(10, 31),
            log_by_default=False,
        )

    # cerebro.addstrategy(DelayedIndexing)
    cerebro.addstrategy(PlayWithIndicators)
    # cerebro.addstrategy(EmptyCall)
    # cerebro.addstrategy(TestUsingOperators)

    # Print out the starting conditions
    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():,.2f}")

    # Run over everything
    # maxcpus=1 is important when multiple variants are used via optstrategy
    # are being analyzed
    cerebro.run(maxcpus=1)

    print("Trade Results:")

    if debug:
        df: pd.DataFrame = cerebro.runstrats[0][0].trade_results
        print(df)
        print(f"Profit (w/o commission):\t{df.pnl.sum():,.2f}")
        print(f"Profit (incl. commission)\t{df.pnlcomm.sum():,.2f}")

        # Print out the final result
        print(f"Final Portfolio Value: {cerebro.broker.getvalue():,.2f}")

    # cerebro.plot()

    if debug:  # Print out the final result
        print("#\tDate\t\tOpen\tHigh\tLow\tClose\t\tVolume\tAdj Close")
        for i in range(len(data_0)):
            x = data_0._load()
            print(
                f"{i}\t{data_0.datetime.date(0)}\t{data_0.open[0]:.2f}\t"
                f"{data_0.high[0]:.2f}\t{data_0.low[0]:.2f}\t{data_0.close[0]:.2f}\t"
                f"{data_0.volume[0]:.2f}\t{data_0.close[0]:.2f}"
            )
