# -*- coding: UTF-8 -*-
# https://www.backtrader.com/docu/quickstart/quickstart/#adding-a-data-feed

# import
from datetime import datetime  # For datetime objects
from pathlib import Path
from colorama import Fore, Style
import inspect
import pandas as pd

import backtrader as bt


# globals

# functions
# Create a Strategy
class TestStrategy(bt.Strategy):
    params = (
        ('days_decline', 3),
        ('exitbars', 5),
    )

    def __init__(self):
        # Keep a reference to the "close" line (column) in the data[0] data series
        # self.data is equivalent to self.datas[0] or self.data_0, if there is more than one data feed
        self.dataclose = self.data.close

        # To keep track of pending orders
        self.order = None

        # 105
        # self.buyprice = None
        # self.buycomm = None

        # 105a For logging trade results only
        self.trade_results = pd.DataFrame({
            'date': pd.Series(dtype='str'),
            'price': pd.Series(dtype='float64'),
            'pnl': pd.Series(dtype='float64'),
            'pnlcomm': pd.Series(dtype='float64')
        }
        )

    def log(self, txt, dt=None):
        """
        Logging function for this strategy
        """
        caller = inspect.stack()[1].function
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{len(self):3} {caller:15}\t{dt.strftime('%d.%m.%Y')} {txt}')

    def next(self):
        """
        Die Methode next() in einer Backtrader-Strategie wird bei jedem neuen Datenpunkt (Bar) aufgerufen und enthält
        die Handelslogik der Strategie.
        Die next()-Methode überprüft den aktuellen Marktstatus, entscheidet basierend auf der definierten Handelslogik,
        ob Kauf- oder Verkaufsorders erstellt werden sollen, und loggt relevante Informationen.
        """
        # Log the closing price of the series from the reference
        # self.log(f'{Style.DIM}Close {self.dataclose[0]:,.2f}{Style.RESET_ALL}\tNumber of bars processed: {len(self)}')
        self.log(f'{self.data.open[0]:,.2f} {self.data.high[0]:,.2f} {self.data.low[0]:,.2f}'
                 f' {Style.BRIGHT}{self.data.close[0]:,.2f}{Style.NORMAL}  Vol: {self.data.volume[0]:,.2f}')

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            self.log(f'{Fore.RED}Order pending: {self.order.isbuy()}{Fore.RESET}')
            return

        # Check if we are in the market. Every completed order creates a position?
        if not self.position:
            # Check if the closing prices have decreased over the last `days_decline` bars
            decline = all(self.dataclose[-i] < self.dataclose[-(i+1)] for i in range(self.p.days_decline-1))

            if decline:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log(f'{Fore.GREEN}Create BUY order {self.dataclose[0]:,.2f}{Fore.RESET}')
                self.order = self.buy()
        else:
            # Already in the market (positions exist) ... we might sell
            if len(self) >= (self.bar_executed + self.p.exitbars):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log(f'{Fore.YELLOW}Create SELL order {self.dataclose[0]:,.2f}{Fore.RESET}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

    def notify_order(self, order):
        """
        The order lifecycle is managed through the notify_order method,
        which is called whenever the status of an order changes.
        This ensures that the strategy can react to order completions, rejections, or cancellations in a controlled manner.
        Here is a brief overview of how orders are processed:
            - Order Submission: Orders are submitted within the next method.
            - Order Notification: The notify_order method is called to update the status of the order.
            - Order Execution: Orders are executed based on the market data and broker conditions.
        This synchronous processing ensures that the strategy can manage orders and positions in a
        predictable and sequential manner.

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
            self.log(f'{Style.BRIGHT}{action} order executed at {order.executed.price:,.2f}'
                     f'\tCommission: {order.executed.comm:,.2f} {Style.RESET_ALL}')

            # 105
            if order.isbuy():
                pass
                # self.buyprice = order.executed.price
                # self.buycomm = order.executed.comm

            # len(self) is the number of bars processed
            self.bar_executed = len(self)  # Save the bar where the order was executed

        elif order.status in {order.Canceled, order.Margin, order.Rejected}:
            self.log(f'{Fore.RED}Order note executed! Status = {order.status} (Canceled/Margin/Rejected){Fore.RESET}')

        # Write down: no pending order
        self.order = None

    # 105
    def notify_trade(self, trade):
        """
        The notify_trade method is called whenever there is a change in the status of a trade.
        This method is used to handle and log trade results, such as when a trade is closed or its status changes.
        The method has two primary functions:
            - Logs Trade Results: It logs the results of a trade, including whether it was a profit or loss,
              and the gross and net profit/loss.
            - Updates Trade DataFrame: It updates a DataFrame with the trade details, such as date, price, status,
              and profit/loss.
        notify_trade is Called:
            - Trade Closed: When a trade is closed, the method logs the result and updates the DataFrame.
            - Trade Status Change: When the status of a trade changes, it logs the new status.
        """
        if trade.isclosed:
            result = 'profit' if trade.pnlcomm > 0 else 'loss'
            self.log(
                    f'Trade is closed. Operation {result}, gross: {trade.pnl:,.2f}, net (incl.commission): {trade.pnlcomm:,.2f}'
            )
            # 105a Log the trade results
            new_row = {
                'date': self.datas[0].datetime.date(0).strftime('%d.%m.%Y'),
                'price': float(trade.price),
                'pnl': float(trade.pnl),
                'pnlcomm': float(trade.pnlcomm)
            }

            # Append the new row to the DataFrame
            self.trade_results = self.trade_results._append(new_row, ignore_index=True)

        else:
            self.log(f'Trade status: {trade.status_names[trade.status]}\tNothing to do!')
            return

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
            fromdate=datetime(2000, 1, 1),
            # Do not pass values after this date
            todate=datetime(2000, 12, 31),
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
