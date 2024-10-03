# -*- coding: UTF-8 -*-
# From: https://medium.com/modern-ai/the-coolest-python-library-for-quants-in-2024-3c2f954752d1

# import
import backtrader as bt
import datetime
import yfinance as yf

# globals

# functions
class MomentumStrategy(bt.Strategy):
    params = (
        ('threshold', 0.001),  # Threshold for generating buy/sell signals
        ('size', 10),  # Number of shares to trade
    )

    def __init__(self):
        self.data_close = self.data.close  # We will operate based on close prices
        self.portfolio_values = []  # List to store portfolio values

    def next(self):
        # Append current portfolio value to the list
        self.portfolio_values.append(self.broker.getvalue())

        if not self.position:  # Not in the market
            #
            if self.data_close[-1] < self.data_close[-2] * (1 - self.p.threshold):
                self.buy(size=self.p.size)
        else:  # In the market
            if self.data_close[-1] > self.data_close[-2] * (1 + self.p.threshold):
                self.sell(size=self.p.size)

if __name__ == '__main__':

    # Download the data
    data = yf.download('NVDA', start='2022-01-01', end='2023-12-31')
    # Create a data feed
    data_feed = bt.feeds.PandasData(dataname=data)

    # Initialize Cerebro (the Backtrader engine)
    cerebro = bt.Cerebro()

    # Add the strategy.
    # Threshold is the percentage change in the price that should trigger a buy/sell signal
    # Size is the number of shares to trade
    cerebro.addstrategy(MomentumStrategy, threshold = 0.01, size = 10)

    # Add the data feed
    cerebro.adddata(data_feed)

    # Set the initial cash
    cerebro.broker.setcash(10000)

    # Run the backtest
    results = cerebro.run()

    ## Plot the results
    cerebro.plot()

    # Get the portfolio values from the strategy
    portfolio_values = results[0].portfolio_values

    # Print the portfolio values
    for idx, value in enumerate(portfolio_values):
        print(f"Step {idx + 1}: Portfolio Value: {value:.2f}")