# -*- coding: UTF-8 -*-
# https://www.backtrader.com/docu/quickstart/quickstart/#adding-a-data-feed

# import
import datetime  # For datetime objects
from pathlib import Path
from colorama import Fore, Style
import pandas as pd

import backtrader as bt


# globals

# functions
# Create a Strategy
class TestStrategy(bt.Strategy):
    # TODO understand len(self)

    def log(self, txt, dt=None):
        """
        Logging function for this strategy
        """
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def __init__(self):
        # Keep a reference to the "close" line (column) in the data[0] data series
        self.dataclose = self.datas[0].close

        # To keep track of pending orders
        self.order = None

        # 105
        self.buyprice = None
        self.buycomm = None

        # 105a
        self.trade_results = pd.DataFrame({
            'date': pd.Series(dtype='str'),
            'price': pd.Series(dtype='float64'),
            'status': pd.Series(dtype='str'),
            'pnl': pd.Series(dtype='float64'),
            'pnlcomm': pd.Series(dtype='float64')
        }
        )

    def next(self):
        # Log the closing price of the series from the reference
        self.log(f'{Style.DIM}Close {self.dataclose[0]:,.2f}{Style.RESET_ALL}')

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            self.log(f'{Fore.RED}Order pending: {self.order.isbuy()}{Fore.RESET}')
            return

        # Check if we are in the market. Every completed order creates a position?
        if not self.position:
            # My strategy: Buy if there is are three day close decrease
            if self.dataclose[0] < self.dataclose[-1] < self.dataclose[-2]:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log(f'{Fore.GREEN}Create BUY order {self.dataclose[0]:,.2f}{Fore.RESET}')
                self.order = self.buy()
        else:
            # Already in the market (positions exist) ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log(f'{Fore.YELLOW}Create SELL order {self.dataclose[0]:,.2f}{Fore.RESET}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

    def notify_order(self, order):
        """
        This method will be called whenever an order status changes
        Order details can be analyzed
        """
        action = f'{Fore.GREEN}BUY{Fore.RESET}' if order.isbuy() else f'{Fore.YELLOW}SELL{Fore.RESET}'

        if order.status in {order.Submitted, order.Accepted}:
            self.log(f'{action} order {order.Status[order.status]} to/by broker - Nothing to do')
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status == order.Completed:
            self.log(f'{Style.BRIGHT}{action} order executed at {order.executed.price:,.2f}{Style.RESET_ALL}')

            # 105
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm

            # TODO Verstehen! Ist das die Zeile im Datensatz?
            self.bar_executed = len(self)  # Save the bar where the order was executed

        elif order.status in {order.Canceled, order.Margin, order.Rejected}:
            self.log(f'{Fore.RED}Order note executed! Status = {order.status} (Canceled/Margin/Rejected){Fore.RESET}')

        # Write down: no pending order
        self.order = None

    # 105
    def notify_trade(self, trade):
        """
        Notify the trade result
        """
        if trade.isclosed:
            result = 'profit' if trade.pnlcomm > 0 else 'loss'
            self.log(
                f'Trade is closed. Operation {result}, gross: {trade.pnl:,.2f}, net (incl.commission): {trade.pnlcomm:,.2f}'
                )
        else:
            self.log(f'Trade status: {trade.status_names[trade.status]}\tNothing to do!')
            return

        # 105a
        new_row = {
            'date': self.datas[0].datetime.date(0).isoformat(),
            'price': float(trade.price),
            'status': trade.status_names[trade.status],
            'pnl': float(trade.pnl),
            'pnlcomm': float(trade.pnlcomm)
        }

        # Append the new row to the DataFrame
        self.trade_results = self.trade_results._append(new_row, ignore_index=True)

    def next_simple(self):
        # 104
        # Simply log the closing price of the series from the reference
        # Index [0] is the most recent price
        self.log(txt=f'Close, {self.dataclose[0]:,.2f}')


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

    # 105 Set the commission - 0.1% --> 0.001
    cerebro.broker.setcommission(commission=0.001)

    cerebro.addstrategy(TestStrategy)

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
