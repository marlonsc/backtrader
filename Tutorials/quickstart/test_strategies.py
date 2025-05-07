"""test_strategies.py module.

Description of the module functionality."""


# import

import inspect

import backtrader as bt
import pandas as pd
from colorama import Fore, Style

# from loguru import logger
# from icecream import ic

# globals


# functions/classes
class TestStrategy_SMA(bt.Strategy):
    """Sandbox for different test strategies"""

    params = (
        ("bars_decline", 3),
        ("bars_since_last_sell", 5),
        ("ma_period", 15),
        ("long_period", 25),
        ("log_by_default", True),
        ("delay", 1),
    )

    def __init__(self):
""""""
        """Called when the backtest is finished"""
        final_value = self.broker.getvalue()
        self.log(
            f"(MA Period {self.p.ma_period})\tEnding Value {final_value:,.2f}",
            caller="stop",
            print_it=True,
        )

    def log(self, txt: str, dt=None, caller: str = None, print_it: bool = False):
"""Logging function for this strategy

Args::
    txt: 
    dt: (Default value = None)
    caller: (Default value = None)
    print_it: (Default value = False)"""
    print_it: (Default value = False)"""
        if not print_it and not self.p.log_by_default:
            return

        if caller is None:
            caller = inspect.stack()[1].function

        dt = dt or self.datas[0].datetime.date(0)
        formatted_date = dt.strftime("%d.%m.%Y")
        bars_processed = len(self)

        print(f"{bars_processed:3} {caller:15}\t{formatted_date} {txt}")

    def next(self):
"""The next() method in a Backtrader strategy is called for each new data point (bar) and contains
        the trading logic of the strategy.
        The next() method checks the current market status, decides based on the defined trading logic
        whether buy or sell orders should be created, and logs relevant information."""
        """
        # Log the closing price of the series from the reference
        # self.log(f'{Style.DIM}Close {self.dataclose[0]:,.2f}{Style.RESET_ALL}\tNumber of bars processed: {len(self)}')
        # self.log(f'{self.data.open[0]:,.2f} {self.data.high[0]:,.2f} {self.data.low[0]:,.2f}'
        # f' {Style.BRIGHT}{self.data.close[0]:,.2f}{Style.NORMAL}  Vol:
        # {self.data.volume[0]:,.2f}')

        self.log(
            f"Portfolio: Position size: {self.position.size} shares, Available cash:"
            f" {self.broker.get_cash():,.2f} Investment value:"
            f" {self.broker.get_value() - self.broker.get_cash():,.2f} Portfolio value:"
            f" {self.broker.get_value():,.2f}",
            caller="next",
        )

        # demo for lines.get-method
        # slice = self._dataclose.get(size=5)
        # self.log(f'Close prices: {slice}', caller='next', print_it=True)

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self._order:
            self.log(
                f"{Fore.RED}Order pending: {self._order.isbuy()} No new order"
                f" allowed!{Fore.RESET}",
                caller="func next",
            )
            return

        # 105 Check if the closing prices have decreased over the last `days_decline` bars
        # buy_condition = all(self._dataclose[-i] < self._dataclose[-(i + 1)] for i in range(self.p.bars_decline - 1))
        # sell_condition = len(self) >= (self._bar_executed + self.p.bars_since_last_sell)

        # Check if we are in the market. Every completed BUY order creates a
        # position?
        if not self.position:
            # Not in the market yet... we COULD buy if...
            if self._buy_condition:  # (identisch zu self._buy_condition)
                # BUY, BUY, BUY!!! (with all possible
                # standard parameters)
                buy_order_message = (
                    f"{Fore.GREEN}Creating BUY order"
                    f" {self._dataclose[0]:,.2f}{Fore.RESET}"
                )
                self.log(buy_order_message, caller="func next")
                self._order = self.buy()
        else:
            # Already in the market (positions exist) ... we could
            # sell
            if self._sell_condition:
                # SELL, SELL, SELL!!! (with all possible
                # standard parameters)
                sell_order_message = (
                    f"{Fore.YELLOW}Creating SELL order"
                    f" {self._dataclose[0]:,.2f}{Fore.RESET}"
                )
                self.log(
                    sell_order_message,
                )
                # Track the created order to avoid a second order
                # being placed
                self._order = self.sell()

    def notify_order(self, order):
"""The order lifecycle is managed through the notify_order method,
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

Args::
    order:"""
    order:"""
        action = (
            f"{Fore.GREEN}BUY{Fore.RESET}"
            if order.isbuy()
            else f"{Fore.YELLOW}SELL{Fore.RESET}"
        )

        if order.status in {order.Submitted, order.Accepted}:
            self.log(
                f"{action} order {order.Status[order.status]} to/by broker - Nothing"
                " to do"
            )
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status == order.Completed:
            self.log(
                f"{Style.BRIGHT}{action} order executed at {order.executed.price:,.2f}"
                f"\tCommission: {order.executed.comm:,.2f} {Style.RESET_ALL}"
            )

            # 105
            if order.isbuy():
                pass
                # self.buyprice = order.executed.price
                # self.buycomm = order.executed.comm

            # len(self) is the number of bars processed
            # Save the bar where the order was executed
            self._bar_executed = len(self)

        elif order.status in {order.Canceled, order.Margin, order.Rejected}:
            self.log(
                f"{Fore.RED}Order note executed! Status ="
                f" {order.status} (Canceled/Margin/Rejected){Fore.RESET}"
            )

        # Write down: no pending order
        self._order = None

    # 105
    def notify_trade(self, trade):
"""The notify_trade method is called whenever there is a change in the status of a trade.
This method is used to handle and log trade results, such as when a trade is closed or its status changes.
The method has two primary functions:
- Logs Trade Results: It logs the results of a trade, including whether it was a profit or loss,
and the gross and net profit/loss.
- Updates Trade DataFrame: It updates a DataFrame with the trade details, such as date, price, status,
and profit/loss.
notify_trade is Called:
- Trade Closed: When a trade is closed, the method logs the result and updates the DataFrame.
- Trade Status Change: When the status of a trade changes, it logs the new status.

Args::
    trade:"""
    trade:"""
        if trade.isclosed:
            result = "profit" if trade.pnlcomm > 0 else "loss"
            self.log(
                f"Trade is closed. Operation {result}, gross: {trade.pnl:,.2f}, net"
                f" (incl.commission): {trade.pnlcomm:,.2f}"
            )
            # 105a Log the trade results
            new_row = {
                "date": self.datas[0].datetime.date(0).strftime("%d.%m.%Y"),
                "price": float(trade.price),
                "pnl": float(trade.pnl),
                "pnlcomm": float(trade.pnlcomm),
            }

            # Append the new row to the DataFrame
            self.trade_results = self.trade_results._append(new_row, ignore_index=True)

        else:
            self.log(
                f"Trade status: {trade.status_names[trade.status]}\tNothing to do!"
            )
            return


class DelayedIndexing(TestStrategy_SMA):
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
"""Logging function fot this strategy

Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
""""""
""""""
""""""
"""Logging function fot this strategy

Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
""""""
"""Args::
    order:"""
""""""
""""""
"""Logging function fot this strategy

Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
""""""
"""Args::
    order:"""
"""Args::
    trade:"""
""""""
        # Simply log the closing price of the series from the reference
        self.log("Close, %.2f" % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                # current close less than previous close

                if self.dataclose[-1] < self.dataclose[-2]:
                    # previous close less than the previous close

                    # BUY, BUY, BUY!!! (with default parameters)
                    self.log("BUY CREATE, %.2f" % self.dataclose[0])

                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:
            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log("SELL CREATE, %.2f" % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


if __name__ == "__main__":
    print("This script is not meant to be run directly.")
