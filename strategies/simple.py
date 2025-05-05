#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
"""
BACKTESTING TRADING STRATEGIES WITH POSTGRESQL DATABASE
===============================================================

This script allows you to backtest multiple trading strategies using historical stock data
from a PostgreSQL database. It demonstrates the application of various
technical analysis indicators and trading strategies on any stock symbol with customizable
date ranges.

USAGE:
------
python strategies/simple.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format
--todate, -t    : End date for historical data in YYYY-MM-DD format

OPTIONAL ARGUMENTS:
------------------
--dbuser, -u    : PostgreSQL username (default: jason)
--dbpass, -pw   : PostgreSQL password (default: fsck)
--dbname, -n    : PostgreSQL database name (default: market_data)
--cash, -c      : Initial cash for the strategy (default: $100,000)
--commission, -cm: Commission rate as a decimal (default: 0.001 or 0.1%)
--single, -s    : Run only a single strategy instead of all (options below)
--plot, -pl     : Plot the results (not currently implemented)

AVAILABLE STRATEGIES:
-------------------
1. Linear Combination Signal (--single lincomb)
   A composite strategy that combines three crossover signals:
   - Long and Short moving average crossover
   - Short moving average and price crossover
   - Long moving average and price crossover

   Parameters:
   - long_ravg: Period for long moving average (default: 25)
   - short_ravg: Period for short moving average (default: 12)
   - spike_window: Window to smooth crossover signals (default: 4)
   - cls, csr, clr: Weights for each signal component (defaults: 0.5, -0.1, -0.3)

   Trading Logic:
   - Buy when the combined signal is positive
   - Sell when the combined signal is negative

2. Relative Strength Index (--single rsi)
   A momentum oscillator that measures the speed and change of price movements,
   typically used to identify overbought or oversold conditions.

   Parameters:
   - min_RSI: Lower threshold for oversold condition (default: 35)
   - max_RSI: Upper threshold for overbought condition (default: 65)
   - look_back_period: Period for RSI calculation (default: 14)

   Trading Logic:
   - Buy when RSI falls below min_RSI (oversold)
   - Sell when RSI rises above max_RSI (overbought)

3. Moving Average Convergence Divergence (--single macd)
   A trend-following momentum indicator that shows the relationship
   between two moving averages of a security's price.

   Parameters:
   - fast_LBP: Period for fast EMA (default: 12)
   - slow_LBP: Period for slow EMA (default: 26)
   - signal_LBP: Period for signal line (default: 9)

   Trading Logic:
   - Buy when MACD line crosses above signal line
   - Sell when MACD line crosses below signal line

EXAMPLES:
---------
1. Run all strategies on Apple stock for the year 2023:
   python strategies/simple.py --data AAPL --fromdate 2023-01-01 --todate 2023-12-31

2. Run only the RSI strategy on Tesla stock for Q1 2023:
   python strategies/simple.py --data TSLA --fromdate 2023-01-01 --todate 2023-03-31 --single rsi

3. Run MACD strategy on NVIDIA with a higher initial cash amount:
   python strategies/simple.py --data NVDA --fromdate 2022-01-01 --todate 2022-12-31 --single macd --cash 200000

OUTPUT:
-------
For each strategy, the script will display:
- Starting portfolio value
- Trade entries and exits with prices
- Final portfolio value
- Return percentage
- Sharpe ratio (when available)
- Maximum drawdown
- A comparison ranking the strategies by performance

NOTES:
------
- The script currently has three fully implemented strategies (lincomb, rsi, macd).
- Additional strategies are included in the code but are currently disabled.
- Performance results are based on historical data and do not guarantee future results.
- No transaction costs or slippage are considered beyond the simple commission rate.

"""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import argparse
import datetime

import backtrader as bt
import pandas as pd
import psycopg2
import psycopg2.extras


class StockPriceData(bt.feeds.PandasData):
    """Stock Price Data Feed"""

    params = (
        ("datetime", None),  # Column containing the date (index)
        ("open", "Open"),  # Column containing the open price
        ("high", "High"),  # Column containing the high price
        ("low", "Low"),  # Column containing the low price
        ("close", "Close"),  # Column containing the close price
        ("volume", "Volume"),  # Column containing the volume
        ("rsi", "RSI"),  # Column containing the RSI value
        ("openinterest", None),  # Column for open interest (not available)
    )


def get_db_data(symbol, dbuser, dbpass, dbname, fromdate, todate):
    """Get historical price data from PostgreSQL database

    :param symbol:
    :param dbuser:
    :param dbpass:
    :param dbname:
    :param fromdate:
    :param todate:

    """
    # Format dates for database query
    from_str = fromdate.strftime("%Y-%m-%d %H:%M:%S")
    to_str = todate.strftime("%Y-%m-%d %H:%M:%S")

    print(
        f"Fetching data from PostgreSQL database for {symbol} from {from_str} to"
        f" {to_str}"
    )

    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            host="localhost", user=dbuser, password=dbpass, database=dbname
        )

        # Create a cursor to execute queries
        cursor = connection.cursor()

        # Query the data
        query = """
        SELECT date, open, high, low, close, volume, rsi
        FROM stock_price_data
        WHERE symbol = %s AND date BETWEEN %s AND %s
        ORDER BY date ASC
        """

        # Execute the query
        cursor.execute(query, (symbol, from_str, to_str))
        rows = cursor.fetchall()

        # Check if any data was retrieved
        if not rows:
            raise Exception(f"No data found for {symbol} in the specified date range")

        # Convert to pandas DataFrame
        df = pd.DataFrame(
            rows,
            columns=["Date", "Open", "High", "Low", "Close", "Volume", "RSI"],
        )

        # Convert 'Date' to datetime and set as index
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")

        # Ensure numeric data types
        df["Open"] = pd.to_numeric(df["Open"])
        df["High"] = pd.to_numeric(df["High"])
        df["Low"] = pd.to_numeric(df["Low"])
        df["Close"] = pd.to_numeric(df["Close"])
        df["Volume"] = pd.to_numeric(df["Volume"])
        df["RSI"] = pd.to_numeric(df["RSI"])

        print(f"Successfully fetched data for {symbol}. Retrieved {len(df)} bars.")

        # Close the database connection
        cursor.close()
        connection.close()

        return df

    except psycopg2.Error as err:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        raise Exception(f"Database error: {err}")
    except Exception as e:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        raise Exception(f"Error fetching data: {e}")


class LinComb_Signal(bt.Strategy):
    """ """

    params = (
        ("long_ravg", 25),
        ("short_ravg", 12),
        ("max_position", 10),
        ("spike_window", 4),
        ("cls", 0.5),
        ("csr", -0.1),
        ("clr", -0.3),
        ("printlog", False),
    )

    def log(self, txt, dt=None):
        """

        :param txt:
        :param dt:  (Default value = None)

        """
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        self.long_RAVG = bt.indicators.SMA(
            self.data.close,
            period=self.params.long_ravg,
            plotname="Long Returns Avg",
        )
        self.short_RAVG = bt.indicators.SMA(
            self.data.close,
            period=self.params.short_ravg,
            plotname="Short Returns Avg",
        )

        # Long and Short Cross signal
        self.ls_cross = bt.indicators.CrossOver(
            self.long_RAVG, self.short_RAVG, plotname="LS crossover"
        )
        self.ls_cross_SMA = bt.indicators.SMA(
            self.ls_cross, period=self.params.spike_window, plotname="LS_Spike"
        )

        # Short and Close Cross signal
        self.sr_cross = bt.indicators.CrossOver(
            self.short_RAVG, self.data.close, plotname="SR crossover"
        )
        self.sr_cross_SMA = bt.indicators.SMA(
            self.sr_cross, period=self.params.spike_window, plotname="SR_Spike"
        )

        # Long and Close Cross signal
        self.lr_cross = bt.indicators.CrossOver(
            self.long_RAVG, self.data.close, plotname="LR crossover"
        )
        self.lr_cross_SMA = bt.indicators.SMA(
            self.lr_cross, period=self.params.spike_window, plotname="LR_Spike"
        )

    def notify_order(self, order):
        """

        :param order:

        """
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
        # Create the signal with linear combination of other crossings
        signal = (
            self.params.cls * self.ls_cross
            + self.params.clr * self.lr_cross
            + self.params.csr * self.sr_cross
        )

        # Buy sell Logic
        if signal > 0 and self.position.size <= 0:
            # BUY, BUY, BUY!!! (with all possible default parameters)
            self.log("BUY CREATE, %.2f" % self.data.close[0])

            # Keep track of the created order to avoid a 2nd order
            self.order = self.buy(size=self.params.max_position)

        elif signal < 0 and self.position.size > 0:
            # SELL, SELL, SELL!!! (with all possible default parameters)
            self.log("SELL CREATE, %.2f" % self.data.close[0])

            # Keep track of the created order to avoid a 2nd order
            self.order = self.sell(size=self.params.max_position)


class RSI(bt.Strategy):
    """ """

    params = (
        ("min_RSI", 35),
        ("max_RSI", 65),
        ("max_position", 10),
        ("look_back_period", 14),
        ("printlog", False),
    )

    def log(self, txt, dt=None):
        """

        :param txt:
        :param dt:  (Default value = None)

        """
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        # RSI indicator
        self.RSI = bt.indicators.RSI_SMA(
            self.data.close, period=self.params.look_back_period
        )

    def notify_order(self, order):
        """

        :param order:

        """
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

        # Buy if over sold
        if self.RSI < self.params.min_RSI:
            self.buy()

        # Sell if over buyed
        if self.RSI > self.params.max_RSI:
            self.close()


class MACD(bt.Strategy):
    """ """

    params = (
        ("fast_LBP", 12),
        ("slow_LBP", 26),
        ("max_position", 1),
        ("signal_LBP", 9),
        ("printlog", False),
    )

    def log(self, txt, dt=None):
        """

        :param txt:
        :param dt:  (Default value = None)

        """
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        self.fast_EMA = bt.indicators.EMA(self.data, period=self.params.fast_LBP)
        self.slow_EMA = bt.indicators.EMA(self.data, period=self.params.slow_LBP)

        self.MACD = self.fast_EMA - self.slow_EMA
        self.Signal = bt.indicators.EMA(self.MACD, period=self.params.signal_LBP)
        self.Crossing = bt.indicators.CrossOver(
            self.MACD, self.Signal, plotname="Buy_Sell_Line"
        )
        self.Hist = self.MACD - self.Signal

    def notify_order(self, order):
        """

        :param order:

        """
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

        # If MACD is above Signal line
        if self.Crossing > 0:
            if self.position.size < self.params.max_position:
                self.buy()

        # If MACD is below Signal line
        elif self.Crossing < 0:
            if self.position.size > 0:
                self.close()


class Conventional_MA(bt.Strategy):
    """ """

    params = (("maperiod", 25),)

    def log(self, txt, dt=None):
        """Printing function for the complete strategy

        :param txt:
        :param dt:  (Default value = None)

        """
        dt = dt or self.datas[0].datetime.date(0)
        print("%s %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Adding SMA indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod
        )

    def notify_order(self, order):
        """

        :param order:

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

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

            else:
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f"
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
        """

        :param trade:

        """
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    def next(self):
        """ """
        self.log("Close, %.2f" % self.dataclose[0])

        if self.order:
            return

        # check if we are in market
        if not self.position:
            if self.dataclose[0] > self.sma[0]:
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.order = self.buy()
        else:
            if self.dataclose[0] < self.sma[0]:
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.order = self.sell()


class Crossover_MA(bt.Strategy):
    """ """

    params = (("smallmaperiod", 25), ("longmaperiod", 100))

    def log(self, txt, dt=None):
        """Printing function for the complete strategy

        :param txt:
        :param dt:  (Default value = None)

        """
        dt = dt or self.datas[0].datetime.date(0)
        print("%s %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Adding SMA indicator
        self.smallsma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.smallmaperiod
        )
        self.longsma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.longmaperiod
        )

    def notify_order(self, order):
        """

        :param order:

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

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

            else:
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f"
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
        """

        :param trade:

        """
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    def next(self):
        """ """
        self.log("Close, %.2f" % self.dataclose[0])

        if self.order:
            return

        # check if we are in market
        if not self.position:
            if self.smallsma[0] > self.longsma[0]:
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.order = self.buy()
        else:
            if self.smallsma[0] < self.longsma[0]:
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.order = self.sell()


class my_EMA(bt.Strategy):
    """ """

    params = (("maperiod", 35),)

    def log(self, txt, dt=None):
        """Printing function for the complete strategy

        :param txt:
        :param dt:  (Default value = None)

        """
        dt = dt or self.datas[0].datetime.date(0)
        print("%s %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Adding SMA indicator
        self.sma = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=self.params.maperiod
        )

    def notify_order(self, order):
        """

        :param order:

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

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

            else:
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f"
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
        """

        :param trade:

        """
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    def next(self):
        """ """
        self.log("Close, %.2f" % self.dataclose[0])

        if self.order:
            return

        # check if we are in market
        if not self.position:
            if self.dataclose[0] > self.sma[0]:
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.order = self.buy()
        else:
            if self.dataclose[0] < self.sma[0]:
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.order = self.sell()


class WMA(bt.Strategy):
    """ """

    params = (("maperiod", 30),)

    def log(self, txt, dt=None):
        """Printing function for the complete strategy

        :param txt:
        :param dt:  (Default value = None)

        """
        dt = dt or self.datas[0].datetime.date(0)
        print("%s %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Adding SMA indicator
        self.sma = bt.indicators.WeightedMovingAverage(
            self.datas[0], period=self.params.maperiod
        )

    def notify_order(self, order):
        """

        :param order:

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

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

            else:
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f"
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
        """

        :param trade:

        """
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    def next(self):
        """ """
        self.log("Close, %.2f" % self.dataclose[0])

        if self.order:
            return

        # check if we are in market
        if not self.position:
            if self.dataclose[0] > self.sma[0]:
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.order = self.buy()
        else:
            if self.dataclose[0] < self.sma[0]:
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.order = self.sell()


class BB_strat(bt.Strategy):
    """ """

    params = (("maperiod", 30),)

    def log(self, txt, dt=None):
        """Printing function for the complete strategy

        :param txt:
        :param dt:  (Default value = None)

        """
        dt = dt or self.datas[0].datetime.date(0)
        print("%s %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Adding SMA indicator
        self.bbands = bbands = bt.indicators.BBands(self.datas[0])

    def notify_order(self, order):
        """

        :param order:

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

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

            else:
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f"
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
        """

        :param trade:

        """
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    def next(self):
        """ """
        self.log("Close, %.2f" % self.dataclose[0])

        if self.order:
            return

        # check if we are in market
        if not self.position:
            if self.bbands[0] < self.dataclose[0]:
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.order = self.buy()
        else:
            if self.bbands[0] > self.dataclose[0]:
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.order = self.sell()


class Counter_bb(bt.Strategy):
    """ """

    params = (("maperiod", 30),)

    def log(self, txt, dt=None):
        """Printing function for the complete strategy

        :param txt:
        :param dt:  (Default value = None)

        """
        dt = dt or self.datas[0].datetime.date(0)
        print("%s %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Adding SMA indicator
        self.bbands = bbands = bt.indicators.BBands(self.datas[0])

    def notify_order(self, order):
        """

        :param order:

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

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

            else:
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f"
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
        """

        :param trade:

        """
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    def next(self):
        """ """
        self.log("Close, %.2f" % self.dataclose[0])

        if self.order:
            return

        # check if we are in market
        if not self.position:
            if self.bbands[0] > self.dataclose[0]:
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.order = self.buy()
        else:
            if self.bbands[0] < self.dataclose[0]:
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.order = self.sell()


def run_strategy(strategy_class, data, strategy_name, **kwargs):
    """Run a backtest for a specific strategy

    :param strategy_class:
    :param data:
    :param strategy_name:
    :param **kwargs:

    """
    print("\n" + "=" * 50)
    print(f"Running {strategy_name} Strategy")
    print("=" * 50)

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add the data feed to cerebro
    cerebro.adddata(data)

    # Add strategy to cerebro
    # Check if the strategy class already has printlog in its params
    if hasattr(strategy_class.params, "printlog"):
        all_kwargs = {"printlog": True}
        all_kwargs.update(kwargs)
        cerebro.addstrategy(strategy_class, **all_kwargs)
    else:
        # If not, just pass the kwargs without printlog
        cerebro.addstrategy(strategy_class, **kwargs)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Add a commission (0.1%)
    cerebro.broker.setcommission(commission=0.001)

    # Add analyzer
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharperatio")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

    # Print out the starting conditions
    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")

    # Run the backtest
    results = cerebro.run()
    strat = results[0]

    # Print out the final result
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: {final_value:.2f}")

    # Extract analyzer results safely with error handling
    try:
        returns = strat.analyzers.returns.get_analysis()
        total_return = returns.get("rtot", 0)
        if total_return is not None:
            print(f"Return: {total_return * 100:.2f}%")
        else:
            print("Return: N/A")
    except Exception as e:
        print(f"Unable to calculate return: {e}")

    try:
        sharpe = strat.analyzers.sharperatio.get_analysis()
        sharpe_ratio = sharpe.get("sharperatio", None)
        if sharpe_ratio is not None:
            print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
        else:
            print("Sharpe Ratio: N/A")
    except Exception as e:
        print(f"Unable to calculate Sharpe ratio: {e}")

    try:
        drawdown = strat.analyzers.drawdown.get_analysis()
        max_dd = drawdown.get("max", {})
        max_drawdown = max_dd.get("drawdown", None)
        if max_drawdown is not None:
            print(f"Max Drawdown: {max_drawdown:.2f}%")
        else:
            print("Max Drawdown: N/A")
    except Exception as e:
        print(f"Unable to calculate Max Drawdown: {e}")

    return final_value


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=(
            "Backtest multiple trading strategies with data from PostgreSQL database"
        )
    )

    parser.add_argument(
        "--data", "-d", default="AAPL", help="Stock symbol to retrieve data for"
    )

    parser.add_argument("--dbuser", "-u", default="jason", help="PostgreSQL username")

    parser.add_argument("--dbpass", "-pw", default="fsck", help="PostgreSQL password")

    parser.add_argument(
        "--dbname", "-n", default="market_data", help="PostgreSQL database name"
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        default="2020-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        default="2020-12-31",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--cash", "-c", default=100000.0, type=float, help="Starting cash"
    )

    parser.add_argument(
        "--commission",
        "-cm",
        default=0.001,
        type=float,
        help="Commission (percentage)",
    )

    parser.add_argument("--plot", "-pl", action="store_true", help="Plot the results")

    parser.add_argument(
        "--single",
        "-s",
        default=None,
        help=(
            "Run only a single strategy (options: lincomb, rsi, macd, conventional_ma,"
            " crossover_ma, ema, wma, bb, counter_bb)"
        ),
    )

    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()

    # Convert dates
    fromdate = datetime.datetime.strptime(args.fromdate, "%Y-%m-%d")
    todate = datetime.datetime.strptime(args.todate, "%Y-%m-%d")

    # Fetch data from PostgreSQL database
    try:
        df = get_db_data(
            args.data, args.dbuser, args.dbpass, args.dbname, fromdate, todate
        )
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # Create data feed
    data = StockPriceData(dataname=df)

    # Define strategies to run
    strategies = {
        "lincomb": {
            "class": LinComb_Signal,
            "name": "Linear Combination Signal",
        },
        "rsi": {"class": RSI, "name": "Relative Strength Index"},
        "macd": {
            "class": MACD,
            "name": "Moving Average Convergence Divergence",
        },
    }

    # Only add strategies that worked with our parameter handling
    # Uncomment these when they're fixed
    # 'conventional_ma': {'class': Conventional_MA, 'name': 'Conventional Moving Average'},
    # 'crossover_ma': {'class': Crossover_MA, 'name': 'Moving Average Crossover'},
    # 'ema': {'class': my_EMA, 'name': 'Exponential Moving Average'},
    # 'wma': {'class': WMA, 'name': 'Weighted Moving Average'},
    # 'bb': {'class': BB_strat, 'name': 'Bollinger Bands'},
    # 'counter_bb': {'class': Counter_bb, 'name': 'Counter Trend Bollinger Bands'},

    # Run all strategies or just one if specified
    results = {}

    if args.single:
        if args.single in strategies:
            strategy = strategies[args.single]
            results[args.single] = run_strategy(
                strategy["class"], data, strategy["name"]
            )
        else:
            print(f"Unknown strategy: {args.single}")
            print(f"Available strategies: {', '.join(strategies.keys())}")
    else:
        for key, strategy in strategies.items():
            try:
                results[key] = run_strategy(strategy["class"], data, strategy["name"])
            except Exception as e:
                print(f"Error running {strategy['name']}: {e}")
                continue

    # Compare results
    if len(results) > 1:
        print("\n" + "=" * 50)
        print("Strategy Comparison")
        print("=" * 50)

        # Sort strategies by performance
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        for i, (strategy, value) in enumerate(sorted_results):
            print(f"{i + 1}. {strategies[strategy]['name']}: ${value:.2f}")


if __name__ == "__main__":
    main()
