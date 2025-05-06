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
"""GAUSSIAN CHANNEL STRATEGY WITH STOCHASTIC RSI AND BOLLINGER BANDS - (bb-medium)
================================================================================
This strategy uses a more complex triple confirmation method: ascending Gaussian channel + price
above upper band + StochRSI extreme readings. The name should reflect this multiple-indicator
confirmation approach.
This script implements a more advanced trading strategy that combines:
1. Gaussian Channel indicator
2. Stochastic RSI
3. Bollinger Bands
STRATEGY LOGIC:
--------------
- Go LONG when:
a. The gaussian channel is green (filt > filt[1])
b. The close price is above the high gaussian channel band
c. The Stochastic RSI is above 80 or below 20
- Exit LONG (go flat) when the close price crosses below the high gaussian channel band
- No short positions are taken
USAGE:
------
python strategies/bb-medium.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]
REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2018-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2069-12-31)
OPTIONAL ARGUMENTS:
------------------
--dbuser, -u    : PostgreSQL username (default: jason)
--dbpass, -pw   : PostgreSQL password (default: fsck)
--dbname, -n    : PostgreSQL database name (default: market_data)
--cash, -c      : Initial cash for the strategy (default: $100,000)
--bblength, -bl : Period for Bollinger Bands calculation (default: 20)
--bbmult, -bm   : Multiplier for Bollinger Bands standard deviation (default: 2.0)
--matype, -mt   : Moving average type for basis (default: SMA, options: SMA, EMA, WMA, SMMA)
--rsilength, -rl: Period for RSI calculation (default: 14)
--stochlength, -sl: Period for Stochastic calculation (default: 14)
--smoothk, -sk  : Smoothing K period for Stochastic RSI (default: 3)
--smoothd, -sd  : Smoothing D period for Stochastic RSI (default: 3)
--poles, -po    : Number of poles for Gaussian Filter (default: 4, range: 1-9)
--period, -pe   : Sampling period for Gaussian Filter (default: 144, min: 2)
--trmult, -tm   : Multiplier for Filtered True Range (default: 1.414)
--lag, -lg      : Enable reduced lag mode (default: False)
--fast, -fa     : Enable fast response mode (default: False)
--plot, -p      : Generate and show a plot of the trading activity
EXAMPLE:
--------
python strategies/gaussian_triple_confirmation.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --plot"""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import argparse
import datetime
import math
import os
import sys

import backtrader as bt
import pandas as pd
import psycopg2
from strategies.utils import (
    TradeThrottling,
    add_standard_analyzers,
    get_db_data,
    print_performance_metrics,
)

# Add the parent directory to the Python path to import shared modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utility functions


class StockPriceData(bt.feeds.PandasData):
    """Stock Price Data Feed"""

    params = (
        ("datetime", None),  # Column containing the date (index)
        ("open", "Open"),  # Column containing the open price
        ("high", "High"),  # Column containing the high price
        ("low", "Low"),  # Column containing the low price
        ("close", "Close"),  # Column containing the close price
        ("volume", "Volume"),  # Column containing the volume
        ("openinterest", None),  # Column for open interest (not available)
    )


def get_db_data(symbol, dbuser, dbpass, dbname, fromdate, todate):
"""Get historical price data from PostgreSQL database

Args::
    symbol: 
    dbuser: 
    dbpass: 
    dbname: 
    fromdate: 
    todate:"""
    todate:"""
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

        # Query to get the data including RSI
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


class StochasticRSI(bt.Indicator):
    """Stochastic RSI Indicator
Formula:
- RSI = Relative Strength Index
- K = SMA(Stochastic(RSI, RSI, RSI, period), smoothK)
- D = SMA(K, smoothD)"""

    lines = ("k", "d")
    params = (
        ("rsi_length", 14),
        ("stoch_length", 14),
        ("k_smooth", 3),
        ("d_smooth", 3),
    )

    plotinfo = dict(
        plot=True, plotname="Stochastic RSI", subplot=True, plotlinelabels=True
    )

    plotlines = dict(k=dict(color="blue", _name="K"), d=dict(color="orange", _name="D"))

    def __init__(self):
""""""
    """Gaussian Filter indicator as described by John Ehlers
This indicator calculates a filter and channel bands using Gaussian filter techniques"""

    lines = ("filt", "hband", "lband")
    params = (
        ("poles", 4),  # Number of poles (1-9)
        ("period", 144),  # Sampling period (min: 2)
        ("mult", 1.414),  # True Range multiplier
        ("lag_reduction", False),  # Reduced lag mode
        ("fast_response", False),  # Fast response mode
        ("source", None),  # Source data (default: hlc3)
    )

    plotinfo = dict(
        plot=True,
        plotname="Gaussian Channel",
        subplot=False,  # Plot on the same graph as price
        plotlinelabels=True,
    )

    plotlines = dict(
        filt=dict(color="green", _name="Filter", linewidth=2),
        hband=dict(color="red", _name="Upper Band"),
        lband=dict(color="red", _name="Lower Band"),
    )

    def __init__(self):
""""""
    """Strategy that implements the Gaussian Channel with Stochastic RSI trading rules:
- Open long position when:
- The gaussian channel is green (filt > filt[1])
- The close price is above the high gaussian channel band
- The Stochastic RSI is above 80 or below 20
- Multiple exit strategies available (see below)
- Only trades within the specified date range
Exit Strategy Options:
- 'default': Exit when price crosses below the high gaussian channel band
- 'middle_band': Exit when price closes below the middle gaussian channel band (default)
- 'bars': Exit after a specified number of bars
- 'trailing_percent': Exit using a trailing stop based on percentage
- 'trailing_atr': Exit using a trailing stop based on ATR
- 'trailing_ma': Exit when price crosses below a moving average
Position Sizing Options:
- 'percent': Use a fixed percentage of available equity (default 20%)
- 'auto': Size based on volatility (less volatile = larger position)
Additional Features:
- Trade throttling to limit trade frequency
- Risk management with stop loss functionality"""

    params = (
        # Bollinger Bands parameters
        ("bblength", 20),  # Period for Bollinger Bands calculation
        ("bbmult", 2.0),  # Multiplier for standard deviation
        ("bbmatype", "SMA"),  # MA type for basis
        # Stochastic RSI parameters
        ("rsilength", 14),  # Period for RSI calculation
        ("stochlength", 14),  # Period for Stochastic calculation
        ("smoothk", 3),  # Smoothing K period
        ("smoothd", 3),  # Smoothing D period
        # Gaussian Channel parameters
        ("poles", 4),  # Number of poles (1-9)
        ("period", 144),  # Sampling period (min: 2)
        ("trmult", 1.414),  # Filtered True Range multiplier
        ("lag_reduction", False),  # Reduced lag mode
        ("fast_response", False),  # Fast response mode
        # Date range parameters
        ("startdate", datetime.datetime(2018, 1, 1)),  # Start date for trading
        ("enddate", datetime.datetime(2069, 12, 31)),  # End date for trading
        ("printlog", False),  # Print log for each trade
        # Exit strategy parameters
        (
            "exit_strategy",
            "middle_band",
        ),  # Exit strategy: 'default', 'middle_band', 'bars', 'trailing_percent', 'trailing_atr', 'trailing_ma'
        (
            "exit_bars",
            5,
        ),  # Number of bars to hold position when exit_strategy='bars'
        (
            "trailing_percent",
            2.0,
        ),  # Percentage for trailing stop when exit_strategy='trailing_percent'
        (
            "trailing_atr_mult",
            2.0,
        ),  # ATR multiplier for trailing stop when exit_strategy='trailing_atr'
        (
            "trailing_atr_period",
            14,
        ),  # ATR period for trailing stop when exit_strategy='trailing_atr'
        (
            "trailing_ma_period",
            50,
        ),  # MA period for trailing stop when exit_strategy='trailing_ma'
        # Position sizing parameters
        # Position sizing method: 'percent', 'auto'
        ("position_sizing", "percent"),
        (
            "position_percent",
            20.0,
            # Percentage of equity to use per trade (when
            # position_sizing='percent')
        ),
        # Maximum percentage of equity to use per trade
        ("max_position_percent", 95.0),
        (
            "risk_percent",
            1.0,
        ),  # Risk percentage of equity per trade (used in volatility sizing)
        # Trade throttling
        # Minimum hours between trades (0 = no throttling)
        ("trade_throttle_hours", 0),
        # Risk management
        ("use_stop_loss", False),  # Whether to use a stop loss
        ("stop_loss_percent", 5.0),  # Stop loss percentage from entry
        # Extra parameters for ATR indicator
        ("atr_period", 14),  # Period for ATR indicator
    )

    def __init__(self):
""""""
"""Logging function

Args::
    txt: 
    dt: (Default value = None)
    doprint: (Default value = False)"""
    doprint: (Default value = False)"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def notify_order(self, order):
"""Args::
    order:"""
"""Args::
    trade:"""
        """Calculate position size based on selected sizing method"""
        available_cash = self.broker.get_cash()
        current_price = self.dataclose[0]

        if self.p.position_sizing == "percent":
            # Fixed percentage of available equity
            cash_to_use = available_cash * (self.p.position_percent / 100)
            # Make sure we don't exceed maximum position percentage
            cash_to_use = min(
                cash_to_use,
                available_cash * (self.p.max_position_percent / 100),
            )
            size = int(cash_to_use / current_price)
            return size

        elif self.p.position_sizing == "auto":
            # Volatility-based position sizing
            atr_value = self.atr[0]
            if atr_value <= 0:
                # Fallback to fixed percentage if ATR is invalid
                return int(
                    available_cash * (self.p.position_percent / 100) / current_price
                )

            # Calculate position size based on risk percentage and volatility
            risk_amount = self.broker.getvalue() * (self.p.risk_percent / 100)
            risk_per_share = atr_value * self.p.trailing_atr_mult

            if risk_per_share <= 0:
                # Avoid division by zero
                size = int(
                    available_cash * (self.p.position_percent / 100) / current_price
                )
            else:
                size = int(risk_amount / risk_per_share)

            # Calculate the cash required for this position
            position_value = size * current_price

            # Ensure we don't exceed maximum position percentage
            max_position_value = available_cash * (self.p.max_position_percent / 100)
            if position_value > max_position_value:
                size = int(max_position_value / current_price)

            return size

        # Default fallback
        return int(available_cash * (self.p.max_position_percent / 100) / current_price)

    def should_exit_trade(self):
        """Determine if we should exit the trade based on exit strategy"""
        # Default Gaussian Channel strategy (original)
        if self.p.exit_strategy == "default":
            # Close price crosses below the high gaussian channel band
            return (
                self.dataclose[-1] >= self.gaussian.hband[-1]
                and self.dataclose[0] < self.gaussian.hband[0]
            )

        # Middle band exit
        elif self.p.exit_strategy == "middle_band":
            return self.dataclose[0] < self.gaussian.filt[0]

        # Time-based exit
        elif self.p.exit_strategy == "bars":
            return len(self) >= self.exit_bar

        # Trailing stop based exits
        elif self.p.exit_strategy == "trailing_percent":
            # Update the highest price seen since entry
            if self.datahigh[0] > self.highest_price:
                self.highest_price = self.datahigh[0]
                # Update trailing stop
                self.trailing_stop_price = self.highest_price * (
                    1 - self.p.trailing_percent / 100
                )
                self.log(
                    f"TRAILING STOP UPDATED: {self.trailing_stop_price:.2f}",
                    doprint=False,
                )

            # Exit if price touches or goes below the trailing stop
            return self.datalow[0] <= self.trailing_stop_price

        elif self.p.exit_strategy == "trailing_atr":
            # Update the highest price seen since entry
            if self.datahigh[0] > self.highest_price:
                self.highest_price = self.datahigh[0]
                # Update trailing stop
                self.trailing_stop_price = self.highest_price - (
                    self.atr[0] * self.p.trailing_atr_mult
                )
                self.log(
                    f"ATR TRAILING STOP UPDATED: {self.trailing_stop_price:.2f}",
                    doprint=False,
                )

            # Exit if price touches or goes below the trailing stop
            return self.datalow[0] <= self.trailing_stop_price

        elif self.p.exit_strategy == "trailing_ma":
            # Exit when price closes below the moving average
            return self.dataclose[0] < self.trailing_ma[0]

        # Stop loss hit
        if self.p.use_stop_loss and hasattr(self, "stop_loss_price"):
            if self.datalow[0] <= self.stop_loss_price:
                self.log(f"STOP LOSS TRIGGERED: {self.stop_loss_price:.2f}")
                return True

        # Default is to never exit (not realistic but safe)
        return False

    def next(self):
""""""
""""""
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=(
            "Enhanced Gaussian Channel Strategy with Stochastic RSI and Bollinger Bands"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Basic input parameters
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
        default="2018-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        default="2069-12-31",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--cash", "-c", default=100000.0, type=float, help="Starting cash"
    )

    # Bollinger Bands parameters
    parser.add_argument(
        "--bblength",
        "-bl",
        default=20,
        type=int,
        help="Period for Bollinger Bands calculation",
    )

    parser.add_argument(
        "--bbmult",
        "-bm",
        default=2.0,
        type=float,
        help="Multiplier for Bollinger Bands standard deviation",
    )

    parser.add_argument(
        "--matype",
        "-mt",
        default="SMA",
        choices=["SMA", "EMA", "WMA", "SMMA"],
        help="Moving average type for basis",
    )

    # Stochastic RSI parameters
    parser.add_argument(
        "--rsilength",
        "-rl",
        default=14,
        type=int,
        help="Period for RSI calculation",
    )

    parser.add_argument(
        "--stochlength",
        "-sl",
        default=14,
        type=int,
        help="Period for Stochastic calculation",
    )

    parser.add_argument(
        "--smoothk",
        "-sk",
        default=3,
        type=int,
        help="Smoothing K period for Stochastic RSI",
    )

    parser.add_argument(
        "--smoothd",
        "-sd",
        default=3,
        type=int,
        help="Smoothing D period for Stochastic RSI",
    )

    # Gaussian Channel parameters
    parser.add_argument(
        "--poles",
        "-po",
        default=4,
        type=int,
        help="Number of poles for Gaussian Filter (1-9)",
    )

    parser.add_argument(
        "--period",
        "-pe",
        default=144,
        type=int,
        help="Sampling period for Gaussian Filter (min: 2)",
    )

    parser.add_argument(
        "--trmult",
        "-tm",
        default=1.414,
        type=float,
        help="Multiplier for Filtered True Range",
    )

    parser.add_argument(
        "--lag", "-lg", action="store_true", help="Enable reduced lag mode"
    )

    parser.add_argument(
        "--fast", "-fa", action="store_true", help="Enable fast response mode"
    )

    # Exit strategy parameters
    parser.add_argument(
        "--exit_strategy",
        "-es",
        default="middle_band",
        choices=[
            "default",
            "middle_band",
            "bars",
            "trailing_percent",
            "trailing_atr",
            "trailing_ma",
        ],
        help="Exit strategy to use",
    )

    parser.add_argument(
        "--exit_bars",
        "-eb",
        default=5,
        type=int,
        help="Number of bars to hold position when exit_strategy=bars",
    )

    parser.add_argument(
        "--trailing_percent",
        "-tp",
        default=2.0,
        type=float,
        help="Percentage for trailing stop when exit_strategy=trailing_percent",
    )

    parser.add_argument(
        "--trailing_atr_mult",
        "-tam",
        default=2.0,
        type=float,
        help="ATR multiplier for trailing stop when exit_strategy=trailing_atr",
    )

    parser.add_argument(
        "--trailing_atr_period",
        "-tap",
        default=14,
        type=int,
        help="ATR period for trailing stop when exit_strategy=trailing_atr",
    )

    parser.add_argument(
        "--trailing_ma_period",
        "-tmp",
        default=50,
        type=int,
        help="MA period for trailing stop when exit_strategy=trailing_ma",
    )

    # Position sizing parameters
    parser.add_argument(
        "--position_sizing",
        "-ps",
        default="percent",
        choices=["percent", "auto"],
        help="Position sizing method",
    )

    parser.add_argument(
        "--position_percent",
        "-pp",
        default=20.0,
        type=float,
        help="Percentage of equity to use per trade",
    )

    parser.add_argument(
        "--max_position_percent",
        "-mpp",
        default=95.0,
        type=float,
        help="Maximum percentage of equity to use per trade",
    )

    parser.add_argument(
        "--risk_percent",
        "-rp",
        default=1.0,
        type=float,
        help="Risk percentage of equity per trade",
    )

    # Trade throttling
    parser.add_argument(
        "--trade_throttle_hours",
        "-tth",
        default=0,
        type=int,
        help="Minimum hours between trades (0 = no throttling)",
    )

    # Risk management
    parser.add_argument(
        "--use_stop_loss",
        "-usl",
        action="store_true",
        help="Whether to use a stop loss",
    )

    parser.add_argument(
        "--stop_loss_percent",
        "-slp",
        default=5.0,
        type=float,
        help="Stop loss percentage from entry",
    )

    # Plotting
    parser.add_argument(
        "--plot",
        "-p",
        action="store_true",
        help="Generate and show a plot of the trading activity",
    )

    return parser.parse_args()


def main():
    """Main function to run the strategy"""
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

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add the data feed to cerebro
    cerebro.adddata(data)

    # Add strategy with all the enhanced parameters
    cerebro.addstrategy(
        GaussianChannelStrategy,
        # Gaussian Channel parameters
        poles=args.poles,
        period=args.period,
        trmult=args.trmult,
        lag_reduction=args.lag,
        fast_response=args.fast,
        # Bollinger Bands parameters
        bblength=args.bblength,
        bbmult=args.bbmult,
        bbmatype=args.matype,
        # Stochastic RSI parameters
        rsilength=args.rsilength,
        stochlength=args.stochlength,
        smoothk=args.smoothk,
        smoothd=args.smoothd,
        # Date range
        startdate=fromdate,
        enddate=todate,
        printlog=True,
        # Exit strategy parameters
        exit_strategy=args.exit_strategy,
        exit_bars=args.exit_bars,
        trailing_percent=args.trailing_percent,
        trailing_atr_mult=args.trailing_atr_mult,
        trailing_atr_period=args.trailing_atr_period,
        trailing_ma_period=args.trailing_ma_period,
        # Position sizing parameters
        position_sizing=args.position_sizing,
        position_percent=args.position_percent,
        max_position_percent=args.max_position_percent,
        risk_percent=args.risk_percent,
        # Trade throttling
        trade_throttle_hours=args.trade_throttle_hours,
        # Risk management
        use_stop_loss=args.use_stop_loss,
        stop_loss_percent=args.stop_loss_percent,
    )

    # Set our desired cash start
    cerebro.broker.setcash(args.cash)

    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Set slippage to 0 (as required)
    cerebro.broker.set_slippage_perc(0.0)

    # Add standard analyzers with names expected by print_performance_metrics
    add_standard_analyzers(cerebro)

    # Print out the starting conditions
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Print strategy configuration
    print("\nStrategy Configuration:")
    print(f"- Data Source: PostgreSQL database ({args.dbname})")
    print(f"- Symbol: {args.data}")
    print(f"- Date Range: {args.fromdate} to {args.todate}")
    print(
        "- Entry: Gaussian channel is green AND price above upper band AND Stochastic"
        " RSI signal"
    )
    print(f"- Exit Strategy: {args.exit_strategy}")

    if args.exit_strategy == "default":
        print("  (Exit when price crosses below upper Gaussian Channel band)")
    elif args.exit_strategy == "middle_band":
        print("  (Exit when price drops below middle Gaussian Channel band)")
    elif args.exit_strategy == "bars":
        print(f"  (Exit after {args.exit_bars} bars)")
    elif args.exit_strategy == "trailing_percent":
        print(f"  (Using {args.trailing_percent}% trailing stop)")
    elif args.exit_strategy == "trailing_atr":
        print(
            f"  (Using {args.trailing_atr_mult}x ATR({args.trailing_atr_period})"
            " trailing stop)"
        )
    elif args.exit_strategy == "trailing_ma":
        print(f"  (Using {args.trailing_ma_period} period MA as trailing stop)")

    print(f"- Position Sizing: {args.position_sizing}")
    if args.position_sizing == "percent":
        print(f"  (Using {args.position_percent}% of equity per trade)")
    else:
        print(f"  (Auto-sizing based on {args.risk_percent}% risk per trade)")

    if args.trade_throttle_hours > 0:
        print(
            f"- Trade Throttling: Minimum {args.trade_throttle_hours} hours between"
            " trades"
        )

    if args.use_stop_loss:
        print(f"- Stop Loss: {args.stop_loss_percent}% from entry")

    print("\n--- Starting Backtest ---\n")

    # Run the strategy
    results = cerebro.run()

    # Print out final results
    print("\n--- Backtest Results ---\n")
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Use the standardized performance metrics function
    print_performance_metrics(cerebro, results)

    # Plot if requested
    if args.plot:
        cerebro.plot(
            style="candle",
            barup="green",
            bardown="red",
            volup="green",
            voldown="red",
            fill_up="green",
            fill_down="red",
            plotdist=0.5,
            width=16,
            height=9,
        )


if __name__ == "__main__":
    main()
