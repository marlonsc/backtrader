#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2023-2025
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
BOLLINGER BANDS UPPER BREAKOUT STRATEGY - (bb_upper_breakout)
===============================================================

This strategy is based on the Bollinger Bands breakout concept, where prices breaking
out above the upper Bollinger Band are considered a sign of strength and momentum,
potentially signaling the beginning of a new trend.

STRATEGY LOGIC:
--------------
- Go LONG when price CLOSES ABOVE the UPPER Bollinger Band
- Exit LONG when price CLOSES BELOW the LOWER Bollinger Band
- Uses 100% of available capital for positions

MARKET CONDITIONS:
----------------
*** THIS STRATEGY IS SPECIFICALLY DESIGNED FOR TRENDING MARKETS ***
- PERFORMS BEST: During the start of strong uptrends or in momentum-driven markets
- AVOID USING: During sideways/ranging/choppy markets which can lead to false breakouts
- IDEAL TIMEFRAMES: 1-hour, 4-hour, and daily charts
- OPTIMAL MARKET CONDITION: Markets transitioning from consolidation to trend

The strategy will struggle in sideways markets as breakouts are often false and lead
to rapid reversals. This strategy aims to capture the beginning of new trends.

BOLLINGER BANDS:
--------------
Bollinger Bands consist of:
- A middle band (typically a 20-period moving average)
- An upper band (middle band + 2 standard deviations)
- A lower band (middle band - 2 standard deviations)

These bands adapt to volatility - widening during volatile periods and
narrowing during less volatile periods.

USAGE:
------
python strategies/bb_upper_breakout.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2024-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2024-12-31)

DATABASE PARAMETERS:
------------------
--dbuser, -u    : PostgreSQL username (default: jason)
--dbpass, -pw   : PostgreSQL password (default: fsck)
--dbname, -n    : PostgreSQL database name (default: market_data)
--cash, -c      : Initial cash for the strategy (default: $100,000)
--commission, -cm: Commission percentage per trade (default: 0.0)
--interval, -i  : Time interval for data ('1h', '4h', '1d') (default: '1h')

BOLLINGER BANDS PARAMETERS:
-------------------------
--bb-length, -bl: Period for Bollinger Bands calculation (default: 20)
--bb-mult, -bm  : Multiplier for standard deviation (default: 2.0)
--matype, -mt   : Moving average type for Bollinger Bands basis (default: SMA, options: SMA, EMA, WMA, SMMA, VWMA)
--src, -s       : Source for Bollinger Bands calculation (default: "close", options: "open", "high", "low", "close")

OTHER:
-----
--plot, -pl     : Generate and show a plot of the trading activity

EXAMPLE:
--------
python strategies/bb_upper_breakout.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --plot
python strategies/bb_upper_breakout.py --data SPY --fromdate 2024-01-01 --todate 2024-12-31 --commission 0.1 --plot
python strategies/bb_upper_breakout.py --data SPY --fromdate 2024-01-01 --todate 2024-12-31 --interval 4h --plot
python strategies/bb_upper_breakout.py --data SPY --fromdate 2024-01-01 --todate 2024-12-31 --interval 1d
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import datetime
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import backtrader as bt
import backtrader.indicators as btind

# Import utility functions
try:
    # Try direct import first (when running as a module)
    from strategies.utils import (
        get_db_data,
        print_performance_metrics,
        TradeThrottling,
        add_standard_analyzers,
    )
except ModuleNotFoundError:
    # If that fails, try relative import (when running script directly)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from strategies.utils import (
        get_db_data,
        print_performance_metrics,
        TradeThrottling,
        add_standard_analyzers,
    )

# Add the parent directory to the Python path to import shared modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class StockPriceData(bt.feeds.PandasData):
    """
    Stock Price Data Feed
    """

    params = (
        ("datetime", None),  # Column containing the date (index)
        ("open", "Open"),  # Column containing the open price
        ("high", "High"),  # Column containing the high price
        ("low", "Low"),  # Column containing the low price
        ("close", "Close"),  # Column containing the close price
        ("volume", "Volume"),  # Column containing the volume
    )


class BBUpperBreakoutStrategy(bt.Strategy, TradeThrottling):
    """
    Bollinger Bands Upper Breakout Strategy

    This strategy attempts to capture breakouts by:
    1. Buying when price closes above the upper Bollinger Band
    2. Selling when price closes below the lower Bollinger Band

    Strategy Logic:
    - Go LONG when price CLOSES ABOVE the UPPER Bollinger Band
    - Exit LONG when price CLOSES BELOW the LOWER Bollinger Band
    - Uses 100% of available capital for positions

    ** IMPORTANT: This strategy is specifically designed for trending markets **
    It performs poorly in sideways/ranging markets where breakouts are often false.

    Best Market Conditions:
    - Strong uptrending markets with momentum
    - Periods following consolidation or base building
    - Market environments with sector rotation into new leadership
    - Avoid using in choppy, sideways, or range-bound markets
    """

    params = (
        # Bollinger Bands parameters
        ("bb_period", 20),  # Period for Bollinger Bands
        ("bb_dev", 2.0),  # Standard deviations for Bollinger Bands
        ("bb_matype", "SMA"),  # Moving average type for Bollinger Bands
        ("bb_src", "close"),  # Source for Bollinger Bands calculation
        # Date range parameters
        ("start_year", 2024),  # Start year for trading
        ("start_month", 1),  # Start month for trading
        ("start_day", 1),  # Start day for trading
        ("end_year", 2024),  # End year for trading
        ("end_month", 12),  # End month for trading
        ("end_day", 31),  # End day for trading
        # Logging
        ("loglevel", "info"),  # Logging level: debug, info, warning, error
    )

    def log(self, txt, dt=None, level="info"):
        """Logging function"""
        if level == "debug" and self.p.loglevel != "debug":
            return

        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}: {txt}")

    def __init__(self):
        # Store references to price data
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # Select source data based on parameter
        if self.p.bb_src == "open":
            self.datasrc = self.dataopen
        elif self.p.bb_src == "high":
            self.datasrc = self.datahigh
        elif self.p.bb_src == "low":
            self.datasrc = self.datalow
        else:  # default to close
            self.datasrc = self.dataclose

        # Order tracking
        self.order = None

        # For trade throttling
        self.last_trade_date = None

        # For trade tracking
        self.entry_price = None
        self.entry_size = None

        # Commission tracking
        self.total_commission = 0.0

        # Determine MA type for Bollinger Bands
        if self.p.bb_matype == "SMA":
            ma_class = bt.indicators.SimpleMovingAverage
        elif self.p.bb_matype == "EMA":
            ma_class = bt.indicators.ExponentialMovingAverage
        elif self.p.bb_matype == "SMMA (RMA)":
            ma_class = bt.indicators.SmoothedMovingAverage
        elif self.p.bb_matype == "WMA":
            ma_class = bt.indicators.WeightedMovingAverage
        elif self.p.bb_matype == "VWMA":
            ma_class = (
                bt.indicators.WeightedMovingAverage
            )  # Using WMA as proxy for VWMA
        else:
            # Default to SMA
            ma_class = bt.indicators.SimpleMovingAverage

        # Create Bollinger Bands
        self.bbands = bt.indicators.BollingerBands(
            self.datasrc,
            period=self.p.bb_period,
            devfactor=self.p.bb_dev,
            movav=ma_class,
        )

        # For plotting
        self.basis = self.bbands.mid
        self.upper = self.bbands.top
        self.lower = self.bbands.bot

        # Setup date range
        self.start_date = datetime.datetime(
            self.p.start_year, self.p.start_month, self.p.start_day
        )
        self.end_date = datetime.datetime(
            self.p.end_year, self.p.end_month, self.p.end_day
        )

    def is_in_date_range(self):
        """Check if current bar is within the date range"""
        current_date = self.datas[0].datetime.datetime(0)
        return self.start_date <= current_date <= self.end_date

    def calculate_position_size(self):
        """Calculate position size to use 100% of available capital"""
        cash = self.broker.getcash()
        current_price = self.dataclose[0]

        # Use 100% of available capital (minus a small buffer)
        size = int(cash * 0.995 / current_price)
        return max(1, size)  # At least 1 share

    def next(self):
        # Check if we're in the date range
        if not self.is_in_date_range():
            return

        # If an order is pending, we cannot send a new one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # BUY LOGIC: When price closes above upper band
            if self.datasrc[0] > self.bbands.top[0]:
                size = self.calculate_position_size()
                self.log(f"BUY CREATE: {self.dataclose[0]:.2f}, Size: {size}")
                self.order = self.buy(size=size)

                # Update the last trade date for throttling
                self.last_trade_date = self.datas[0].datetime.date(0)
        else:
            # SELL LOGIC: When price closes below lower band
            if self.datasrc[0] < self.bbands.bot[0]:
                self.log(
                    f"SELL CREATE: {self.dataclose[0]:.2f}, Size: {self.position.size}"
                )

                # Use close() instead of sell() to close the entire position
                self.order = self.close()

    def stop(self):
        """Called when backtest is complete"""
        self.log("Bollinger Bands Strategy completed", level="info")
        self.log(f"Final Portfolio Value: {self.broker.getvalue():.2f}", level="info")

        # Add a note about market conditions
        self.log("NOTE: This strategy is designed for trending markets", level="info")
        self.log(
            "      It aims to capture breakouts above the upper band and exit on"
            " reversals",
            level="info",
        )

    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            # Order pending, do nothing
            return

        # Check if order was completed
        if order.status in [order.Completed]:
            # Add commission to total
            self.total_commission += order.executed.comm

            if order.isbuy():
                self.entry_price = (
                    order.executed.price
                )  # Store entry price for P&L calculation
                self.entry_size = order.executed.size  # Store position size
                self.log(
                    f"BUY EXECUTED: Price: {order.executed.price:.2f}, Size:"
                    f" {order.executed.size}, Value: {order.executed.value:.2f}, Comm:"
                    f" {order.executed.comm:.2f}"
                )
            else:  # sell
                if hasattr(self, "entry_price") and self.entry_price is not None:
                    # Calculate profit if we have an entry price
                    profit = (
                        order.executed.price - self.entry_price
                    ) * order.executed.size
                    profit_pct = ((order.executed.price / self.entry_price) - 1.0) * 100
                    self.log(
                        f"SELL EXECUTED: Price: {order.executed.price:.2f}, Size:"
                        f" {order.executed.size}, Value: {order.executed.value:.2f},"
                        f" Comm: {order.executed.comm:.2f}, Profit:"
                        f" ${profit:.2f} ({profit_pct:.2f}%)"
                    )
                else:
                    self.log(
                        f"SELL EXECUTED: Price: {order.executed.price:.2f}, Size:"
                        f" {order.executed.size}, Value: {order.executed.value:.2f},"
                        f" Comm: {order.executed.comm:.2f}"
                    )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order Canceled/Margin/Rejected: {order.status}")

        # Reset order status
        self.order = None

    def notify_trade(self, trade):
        """Track completed trades"""
        if not trade.isclosed:
            return

        self.log(
            f"TRADE COMPLETED: PnL: Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}"
        )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Bollinger Bands Upper Breakout Strategy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Basic input parameters
    parser.add_argument(
        "--data", "-d", required=True, help="Stock symbol to retrieve data for"
    )

    parser.add_argument("--dbuser", "-u", default="jason", help="PostgreSQL username")

    parser.add_argument("--dbpass", "-pw", default="fsck", help="PostgreSQL password")

    parser.add_argument(
        "--dbname", "-n", default="market_data", help="PostgreSQL database name"
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        default="2024-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate", "-t", default="2024-12-31", help="Ending date in YYYY-MM-DD format"
    )

    parser.add_argument(
        "--cash", "-c", default=100000.0, type=float, help="Starting cash"
    )

    parser.add_argument(
        "--commission",
        "-cm",
        default=0.0,
        type=float,
        help="Commission percentage per trade (0.1 = 0.1%)",
    )

    # Time interval parameter
    parser.add_argument(
        "--interval",
        "-i",
        default="1h",
        choices=["1h", "4h", "1d"],
        help="Time interval for data (1h=hourly, 4h=4-hour, 1d=daily)",
    )

    # Bollinger Bands parameters
    parser.add_argument(
        "--bb-length",
        "-bl",
        default=20,
        type=int,
        help="Period for Bollinger Bands calculation",
    )

    parser.add_argument(
        "--bb-mult",
        "-bm",
        default=2.0,
        type=float,
        help="Multiplier for standard deviation",
    )

    parser.add_argument(
        "--matype",
        "-mt",
        default="SMA",
        choices=["SMA", "EMA", "SMMA (RMA)", "WMA", "VWMA"],
        help="Moving average type for Bollinger Bands basis",
    )

    parser.add_argument(
        "--src",
        "-s",
        default="close",
        choices=["open", "high", "low", "close"],
        help="Source for Bollinger Bands calculation",
    )

    # Date range parameters
    parser.add_argument(
        "--start-year", "-sy", default=2024, type=int, help="Start year for trading"
    )

    parser.add_argument(
        "--start-month", "-sm", default=1, type=int, help="Start month for trading"
    )

    parser.add_argument(
        "--start-day", "-sd", default=1, type=int, help="Start day for trading"
    )

    parser.add_argument(
        "--end-year", "-ey", default=2024, type=int, help="End year for trading"
    )

    parser.add_argument(
        "--end-month", "-em", default=12, type=int, help="End month for trading"
    )

    parser.add_argument(
        "--end-day", "-ed", default=31, type=int, help="End day for trading"
    )

    # Plotting
    parser.add_argument(
        "--plot",
        "-pl",
        action="store_true",
        help="Generate and show a plot of the trading activity",
    )

    return parser.parse_args()


def main():
    """Main function to run the backtest"""
    args = parse_args()

    # Convert date strings to datetime objects
    fromdate = datetime.datetime.strptime(args.fromdate, "%Y-%m-%d")
    todate = datetime.datetime.strptime(args.todate, "%Y-%m-%d")

    # Store original dates for reporting
    original_fromdate = fromdate
    original_todate = todate

    # Add padding to ensure we get data for the full date range specified
    # Expand request to start of the year to ensure complete data for Buy & Hold
    padded_fromdate = datetime.datetime(fromdate.year, 1, 1)

    # Get data from database with padded date range and specified interval
    df = get_db_data(
        args.data,
        args.dbuser,
        args.dbpass,
        args.dbname,
        padded_fromdate,
        todate,
        args.interval,
    )

    # Create a Data Feed with date filters
    data = StockPriceData(
        dataname=df, fromdate=original_fromdate, todate=original_todate
    )

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add the data feed to cerebro
    cerebro.adddata(data)

    # Add strategy to cerebro
    cerebro.addstrategy(
        BBUpperBreakoutStrategy,
        # Bollinger Bands parameters
        bb_period=args.bb_length,
        bb_dev=args.bb_mult,
        bb_matype=args.matype,
        bb_src=args.src,
        # Date range parameters
        start_year=args.start_year,
        start_month=args.start_month,
        start_day=args.start_day,
        end_year=args.end_year,
        end_month=args.end_month,
        end_day=args.end_day,
    )

    # Set initial cash
    cerebro.broker.setcash(args.cash)

    # Set commission - percentage value provided as an argument (default 0.0%)
    cerebro.broker.setcommission(commission=args.commission / 100)

    # Set slippage to 0
    cerebro.broker.set_slippage_perc(0.0)

    # Add standard analyzers
    add_standard_analyzers(cerebro)

    # Print out the starting conditions
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Run the strategy
    results = cerebro.run()

    # Get the strategy instance
    strat = results[0]

    # Print final portfolio value
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: ${final_value:.2f}")

    # Print performance metrics with tracked commission
    print_performance_metrics(
        cerebro, results, fromdate=original_fromdate, todate=original_todate
    )

    # Plot if requested
    if args.plot:
        cerebro.plot(style="candlestick", barup="green", bardown="red")


if __name__ == "__main__":
    main()
