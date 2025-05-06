# -*- coding: UTF-8 -*-

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
        """ """
        # Keep a reference to the "close" line (column) in the data[0] data series
        # self.data is equivalent to self.datas[0] or self.data_0, if there is
        # more than one data feed
        self._dataclose = self.datas[0].close

        # To keep track of pending orders
        self._order = None

        # 105
        self._bar_executed = 0
        # self._buyprice = None
        # self._buycomm = None

        # 105a For logging trade results only
        self.trade_results = pd.DataFrame(
            {
                "date": pd.Series(dtype="str"),
                "price": pd.Series(dtype="float64"),
                "pnl": pd.Series(dtype="float64"),
                "pnlcomm": pd.Series(dtype="float64"),
            }
        )

        # 106 Add a Moving Average indicator.
        # Adding an indicator changes the strategy's behavior!
        # A SMA needs a certain number of bars (params.ma_period) to calculate the average.
        # No call to next() will be made until the SMA has enough bars to
        # calculate the average.
        self._sma = bt.indicators.MovingAverageSimple(
            self._dataclose, period=self.p.ma_period
        )

        # Delayed indexing.
        # If I take self._dataclose[-delay] here, the *current* value is taken
        # The formulation here is equivalent to self._dataclose[-1] > self._sma in next()
        # Here a LineOwnOperation is created, not a value (bool)
        self._buy_condition: bt.LineOwnOperation = (
            self._dataclose(-self.p.delay) > self._sma
        )
        self._sell_condition: bt.LineOwnOperation = (
            self._dataclose(-self.p.delay) < self._sma
        )

        # beginregion More Indicators
        # Carefull: Adding indicators might change the strategy's behavior! next() will not be called until all
        # indicators have enough bars to calculate, e.g. the SMA above.
        # Exponential Moving Average = trend indicator
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=self.p.long_period)
        # Weighted Moving Average = trend indicator
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=self.p.long_period, subplot=True)
        # bt.indicators.StochasticSlow(self.datas[0]) # Stochastic Oscillator
        # Moving Average Convergence Divergence = trend indicator as histogram
        # bt.indicators.MACDHisto(self.datas[0])
        # Relative Strength Index = momentum indicator
        # rsi = bt.indicators.RSI(self.datas[0])
        # Smoothed Moving Average of the RSI = trend indicator
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # Average True Range = volatility indicator
        # self._atr = bt.indicators.ATR(self.datas[0],)   # plot=False) # Average True Range
        # endregion

    def stop(self):
        """Called when the backtest is finished"""
        final_value = self.broker.getvalue()
        self.log(
            f"(MA Period {self.p.ma_period})\tEnding Value {final_value:,.2f}",
            caller="stop",
            print_it=True,
        )

    def log(self, txt: str, dt=None, caller: str = None, print_it: bool = False):
        """Logging function for this strategy

Args:
    txt: 
    dt: (Default value = None)
    caller: (Default value = None)
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
        whether buy or sell orders should be created, and logs relevant information.


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

Args:
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

Args:
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
    """ """

    params = (
        ("period", 20),
        ("log_by_default", False),
        ("delay", 1),
    )

    def __init__(self):
        """ """
        self._dataclose = self.data.close
        self._sma = bt.indicators.SimpleMovingAverage(
            self._dataclose, period=self.p.period
        )
        # _cmpval is only calculated in next() (delayed)
        self._cmpval: bt.linebuffer.LinesOperation = (
            self._dataclose(-self.p.delay) > self._sma
        )

    def next(self):
        """ """
        if len(self) < self.p.delay:
            return

        self.log(
            f"Close: {self._dataclose[0]:,.2f}SMA: {self._sma[0]:,.2f}",
            caller="next",
            print_it=False,
        )

        # delayed
        # print(f'Using delayed indexing: {bool(self._cmpval)=}')

        # Using __call__ method
        # Very bad idea, because the calculation is redone _with each call_ and a new
        # object is created. This is not only inefficient, but also error-prone.
        # buy_condition_call:bt.linebuffer.LinesOperatio = self._dataclose(-self.p.delay) > self._sma
        # if len(buy_condition_call) > 0:
        #     print(f'Using __call__: {buy_condition_call[0]=}')
        # else:
        #     print(f'Using __call__: {buy_condition_call=}')

        # Using direct negative indexing
        buy_condition_index: bool = self._dataclose[-self.p.delay] > self._sma
        # self.log(f'Index and delayed call are {"identical" if buy_condition_index == self._cmpval else "different"}', caller='next', print_it=True)
        # print(f'Using direct indexing: {buy_condition_index=}')

        # slice = self._dataclose.get(ago = -1, size=5)
        slice_len = 5
        if len(self) > slice_len + 1:
            my_slice = self._dataclose[-slice_len:]
        self.log(f"Close prices: {my_slice}", caller="next", print_it=True)


class TestUsingOperators(TestStrategy_SMA):
    """ """

    def __init__(self):
        """ """
        super().__init__()

        # operator > overload
        close_over_sma = self._dataclose > self._sma
        print(f"close_over_sma: {type(close_over_sma)=}")
        # operator - overload
        sma_dist_to_high = self._sma - self.data.high
        print(f"sma_dist_to_high: {type(sma_dist_to_high)=}")
        # operator < overload; line-Object of bools
        sma_dist_small = sma_dist_to_high < 3
        print(f"sma_dist_small: {type(sma_dist_small)=}")

        self._sell_signal = bt.indicators.And(close_over_sma, sma_dist_small)
        print(f"sell_signal: {type(self._sell_signal)=}")

    def next(self):
        """ """
        # This strategy does nothing

        action = "SELL" if self._sell_signal else "HOLD"
        self.log(
            f"{action}\tDaily close: {self._dataclose[0]:,.2f} SMA:"
            f" {self._sma[0]:,.2f}",
            caller="TestUsingOperators.next",
            print_it=True,
        )


class MySimpleMovingAverage(bt.indicators.SimpleMovingAverage):
    """ """

    lines = ("sma",)

    params = (
        ("period", 20),
        ("log_by_default", True),
    )

    def __init__(self):
        """ """
        super().__init__()
        print(
            f"Created SimpleMovingAverage with period {self.p.period}",
        )

    def prenext(self):
        """ """
        print("MySimpleMovingAverage.prenext:: current period:", len(self))

    def nextstart(self):
        """ """
        print("MySimpleMovingAverage.nextstart:: current period:", len(self))
        # emulate default behavior ... call next
        self.next()

    def next(self):
        """ """
        print("MySimpleMovingAverage.next:: current period:", len(self))

    def start(self):
        """ """
        self.log(
            f"Current Bar: {len(self):3}",
            caller="MySimpleMovingAverage.start",
            print_it=True,
        )


class PlayWithIndicators(TestStrategy_SMA):
    """ """

    def __init__(self):
        """ """
        self.p.log_by_default = True
        self.sma = MySimpleMovingAverage(self.data, period=20)

    def start(self):
        """ """
        self.log(
            f"Current Bar: {len(self):3}",
            caller="PlayWithIndicators.start",
            print_it=True,
        )

    def next(self):
        """ """
        self.log(
            f"Current Bar: {len(self):3}",
            caller="PlayWithIndicators.next",
            print_it=True,
        )

    def prenext(self):
        """ """
        self.log(
            f"Current Bar: {len(self):3}",
            caller="PlayWithIndicators.prenext",
            print_it=True,
        )

    def nextstart(self):
        """ """
        self.log(
            f"Current Bar: {len(self):3}",
            caller="PlayWithIndicators.nextstart",
            print_it=True,
        )
        # emulates the regular behavior of nextstart()
        self.next()


class EmptyCall(TestStrategy_SMA):
    """ """

    def __init__(self):
        """ """

        # self._buysig = self._dataclose_daily(-self.p.delay) > self._sma
        if len(self.datas) < 2:
            raise Exception(
                "No weekly data to compare with"
            )  # Default to no signal if no weekly data

        self._dataclose_daily = self.data0.close
        self._dataclose_weekly = self.data1.close

        self._sma0 = bt.indicators.SimpleMovingAverage(self._dataclose_daily, period=20)
        self._sma1 = bt.indicators.SimpleMovingAverage(self._dataclose_weekly, period=5)
        # Generates an index error because the data has different lengths
        # sma_daily: 255, sma_weekly: 50
        self._buysig = self._sma0 > self._sma1(-1)

    def next(self):
        """ """
        # This strategy does nothing

        if self._buysig[0] or True:
            self.log(
                f"Daily close: {self._dataclose_daily[0]:,.2f} "
                f"Weekly close: {self._dataclose_weekly[0]:,.2f} "
                f"SMA (Daily): {self._sma0[0]:,.2f} "
                f"SMA (Weekly): {self._sma1[0]:,.2f}",
                caller="next",
                print_it=True,
            )


class TestStrategy_simple(bt.Strategy):
    """ """

    def log(self, txt, dt=None):
        """Logging function fot this strategy

Args:
    txt: 
    dt: (Default value = None)"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        """ """
        # Simply log the closing price of the series from the reference
        self.log("Close, %.2f" % self.dataclose[0])

        if self.dataclose[0] < self.dataclose[-1]:
            # current close less than previous close

            if self.dataclose[-1] < self.dataclose[-2]:
                # previous close less than the previous close

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.buy()


class TestStrategy_104(bt.Strategy):
    """ """

    def log(self, txt, dt=None):
        """Logging function fot this strategy

Args:
    txt: 
    dt: (Default value = None)"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        """Args:
    order:"""
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("BUY EXECUTED, %.2f" % order.executed.price)
            elif order.issell():
                self.log("SELL EXECUTED, %.2f" % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # Write down: no pending order
        self.order = None

    def next(self):
        """ """
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


class TestStrategy_Commission(bt.Strategy):
    """ """

    def log(self, txt, dt=None):
        """Logging function fot this strategy

Args:
    txt: 
    dt: (Default value = None)"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        """Args:
    order:"""
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm,
                    )
                )

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm,
                    )
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None

    def notify_trade(self, trade):
        """Args:
    trade:"""
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    def next(self):
        """ """
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
