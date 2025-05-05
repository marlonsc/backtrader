# -*- coding: UTF-8 -*-

# import
import datetime  # For datetime objects
from pathlib import Path

# Import the backtrader platform
import backtrader as bt

# globals

# functions
# Create a Stratey

if __name__ == "__main__":
    ticker_data = Path.cwd().parent / "datas/orcl-1995-2014.txt"

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy_SMA)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=ticker_data,
        # Do not pass values before this date
        fromdate=datetime.datetime(2000, 1, 1),
        # Do not pass values before this date
        todate=datetime.datetime(2000, 12, 31),
        # Do not pass values after this date
        reverse=False,
    )

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001)

    # Print out the starting conditions
    print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())
