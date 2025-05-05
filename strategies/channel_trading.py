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
PRICE CHANNEL TRADING STRATEGY WITH POSTGRESQL DATABASE - (channel_trading)
===============================================================================

This strategy identifies price channels and trades on rebounds from the channel
boundaries, using dynamic stop-loss levels based on ATR (Average True Range).
It is designed to capture reversions to the mean within a defined price channel.

STRATEGY LOGIC:
--------------
- GO LONG when price rebounds from the lower channel boundary
  (when price touches the lower threshold zone then closes above the open)

- GO SHORT when price rebounds from the upper channel boundary
  (when price touches the upper threshold zone then closes below the open)

- EXIT positions based on:
  1. Take-profit orders at the opposite channel boundary
  2. Stop-loss orders at a multiple of ATR beyond the channel
  3. Trailing stops that lock in profits once a specified profit level is reached

CHANNEL CALCULATION:
------------------
The price channel is defined by:
- Upper Boundary: Highest high over a specified lookback period (default: 20)
- Lower Boundary: Lowest low over the same lookback period
- Channel Midpoint: (Upper Boundary + Lower Boundary) / 2

A short EMA (default: 3) is applied to the boundaries to smooth out noise.

An adjustable threshold (default: 30% from boundary) defines the "rebound zone"
where entries are considered once price action confirms a potential reversal.

RISK MANAGEMENT:
--------------
The strategy employs multi-layered risk management:
- Position sizing based on a fixed risk percentage per trade (default: 2% of account)
- Initial stop-loss levels are set using ATR (Average True Range) to adapt to volatility
- Take-profit levels target the opposite channel boundary or 2:1 reward-to-risk ratio
- Trailing stops lock in profits after a defined profit percentage has been reached

MARKET CONDITIONS:
----------------
- Best suited for range-bound markets with clear support and resistance levels
- Effectiveness diminishes in strong trending markets or during breakouts
- Works across multiple timeframes, but best results typically on 1-hour to daily charts
- Can be applied to various instruments including stocks, forex, and futures

POSITION SIZING:
---------------
The strategy calculates position size dynamically:
- Risk amount = Account value × Risk percentage
- Risk per share = Entry price - Stop loss price
- Position size = Risk amount / Risk per share

This ensures consistent risk exposure regardless of the instrument's volatility
or price level.

USAGE:
------
python strategies/channel_trading.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

REQUIRED ARGUMENTS:
------------------
--data, -d            : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f        : Start date for historical data in YYYY-MM-DD format (default: 2024-01-01)
--todate, -t          : End date for historical data in YYYY-MM-DD format (default: 2024-12-31)

DATABASE PARAMETERS:
------------------
--dbuser, -u          : PostgreSQL username (default: jason)
--dbpass, -pw         : PostgreSQL password (default: fsck)
--dbname, -n          : PostgreSQL database name (default: market_data)
--cash, -c            : Initial cash for the strategy (default: $100,000)

CHANNEL PARAMETERS:
-----------------
--period, -p          : Period for channel calculation (default: 20)
                        This determines how many bars are used to identify the highest high
                        and lowest low. Longer periods create wider, more stable channels.

--devfactor, -df      : Deviation factor for channel width (default: 2.0)
                        Multiplier applied to the channel width for breakout detection.
                        Higher values reduce false breakouts but may miss some opportunities.

--channel-pct, -cp    : How far into channel (0-1) price should reach for signal (default: 0.3)
                        Defines the "rebound zone" within the channel:
                        0.5 = midpoint of channel
                        0.3 = 30% from boundary (closer to edge)
                        0.0 = exactly at the channel boundary

--smooth-period, -sp  : EMA period for smoothing channel boundaries (default: 3)
                        Lower values track the raw channel more closely, higher values
                        smooth out noise but may lag actual boundaries.

ATR PARAMETERS:
-------------
--atr-period, -ap     : ATR calculation period (default: 14)
                        Standard ATR typically uses 14 periods, but can be adjusted
                        to be more responsive (lower) or more stable (higher).

--atr-multiplier, -am : ATR multiplier for stop-loss distance (default: 2.0)
                        Sets initial stop-loss at X times the ATR beyond entry price.
                        Higher values give more room but risk larger losses.

RISK MANAGEMENT:
--------------
--risk-percent, -rp   : Risk per trade as percentage of portfolio (default: 2.0)
                        Controls position sizing to risk consistent percentage per trade.
                        Conservative: 0.5-1.0%, Moderate: 1.0-3.0%, Aggressive: >3.0%

--trail-percent, -tp  : Percentage of profit at which to start trailing stop (default: 50.0)
                        Lower values lock in profits earlier but may exit too soon.
                        Higher values let profits run but risk giving back more gains.

--trail-atr-mult, -tam: ATR multiplier for trailing stop after activation (default: 1.5)
                        Once trailing begins, this sets how tight the trail follows price.
                        Lower values trail more closely but risk being stopped out by noise.

--tp-ratio, -tpr      : Target profit to risk ratio for take-profit level (default: 2.0)
                        Sets take-profit target as X times the risk amount.
                        Common settings: 1.5 (conservative), 2.0 (balanced), 3.0 (ambitious)

BACKTESTING OPTIONS:
------------------
--plot, -pl          : Generate and show a plot of the trading activity
                       Shows price data, channel boundaries, and entry/exit points.

--debug, -db         : Enable detailed debug logging of entry/exit decisions

EXAMPLE COMMANDS:
---------------
1. Standard configuration - default channel trading:
   python strategies/channel_trading.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31

2. Longer timeframe channels - more stable boundaries:
   python strategies/channel_trading.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --channel-period 40 --smooth-period 5

3. Aggressive trading zone - wider rebound area:
   python strategies/channel_trading.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --zone-threshold 0.4

4. Conservative risk management - tighter stops with trailing protection:
   python strategies/channel_trading.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --atr-period 10 --atr-stop 1.5 --profit-target 1.5 --trailing-percent 1.0 --trail-trigger 0.3

5. High-risk approach - larger position sizing with aggressive targets:
   python strategies/channel_trading.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --risk-percent 2.5 --profit-target 3.0 --trail-atr 2.0

Channel customization:
python strategies/channel_trading.py --data AMZN --period 40 --channel-pct 0.2 --smooth-period 5
"""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import argparse
import datetime
import os
import sys

import backtrader as bt
import pandas as pd
import psycopg2
import psycopg2.extras
from strategies.utils import (
    add_standard_analyzers,
    get_db_data,
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
        SELECT date, open, high, low, close, volume
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
            rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"]
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

        print(f"Successfully fetched data for {symbol}. Retrieved {len(df)} bars.")

        # Close the database connection
        cursor.close()
        connection.close()

        return df

    except psycopg2.Error as err:
        if "cursor" in locals():
            cursor.close()
        if "connection" in locals():
            connection.close()
        raise Exception(f"Database error: {err}")
    except Exception as e:
        if "cursor" in locals():
            cursor.close()
        if "connection" in locals():
            connection.close()
        raise Exception(f"Error fetching data: {e}")


class ChannelStrategy(bt.Strategy):
    """Price Channel Trading Strategy

    This strategy identifies price channels and trades on breakouts and rebounds:
    - Buy when price rebounds from the lower channel line
    - Sell when price rebounds from the upper channel line
    - Uses ATR for dynamic stop-loss and take-profit levels


    """

    params = (
        # Channel parameters
        ("period", 20),  # Period for channel calculation
        ("devfactor", 2.0),  # Deviation factor for channel width
        (
            "channel_pct",
            0.3,
        ),  # How far into channel (0-1) price should reach before signal
        ("smooth_period", 3),  # EMA period for smoothing channel boundaries
        # ATR parameters
        ("atr_period", 14),  # ATR period for stop-loss calculation
        ("atr_multiplier", 2.0),  # ATR multiplier for stop-loss distance
        # Risk management
        ("risk_percent", 2.0),  # Risk per trade as percentage of portfolio
        # Percentage of profit at which to start trailing stop
        ("trail_percent", 50.0),
        # ATR multiplier for trailing stop after activation
        ("trail_atr_mult", 1.5),
        ("tp_ratio", 2.0),  # Target profit to risk ratio
        # Logging parameters
        ("log_level", "info"),  # Logging level: 'debug', 'info'
    )

    def log(self, txt, dt=None, level="info"):
        """Logging function for the strategy

        :param txt:
        :param dt:  (Default value = None)
        :param level:  (Default value = "info")

        """
        if level == "debug" and self.p.log_level != "debug":
            return

        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}: {txt}")

    def __init__(self):
        """ """
        # Store price references
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.dataopen = self.datas[0].open

        # Channel indicators
        self.highest_high = bt.indicators.Highest(self.datahigh, period=self.p.period)
        self.lowest_low = bt.indicators.Lowest(self.datalow, period=self.p.period)

        # Apply smoothing to channel boundaries (reduces false signals)
        self.upper_line = bt.indicators.ExponentialMovingAverage(
            self.highest_high, period=self.p.smooth_period
        )
        self.lower_line = bt.indicators.ExponentialMovingAverage(
            self.lowest_low, period=self.p.smooth_period
        )

        # Calculate channel midpoint
        self.midpoint = (self.upper_line + self.lower_line) / 2

        # Channel width
        self.channel_width = self.upper_line - self.lower_line

        # ATR for stop-loss calculation
        self.atr = bt.indicators.ATR(self.datas[0], period=self.p.atr_period)

        # Track orders, stops and positions
        self.buy_order = None
        self.sell_order = None
        self.stop_loss = None
        self.take_profit = None

        # State tracking
        self.channel_top = None
        self.channel_bottom = None
        self.order_price = None
        self.position_size = 0

        # Performance tracking
        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0

    def notify_order(self, order):
        """Handle order notifications

        :param order:

        """
        if order.status in [order.Submitted, order.Accepted]:
            # Order pending, do nothing
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED: Price: {order.executed.price:.2f}, Size:"
                    f" {order.executed.size}, Cost: {order.executed.value:.2f}, Comm:"
                    f" {order.executed.comm:.2f}"
                )
                self.order_price = order.executed.price
                self.position_size = order.executed.size
                # Set stop loss and take profit
                self.set_exit_orders(order.executed.price, is_buy=True)
            else:  # sell
                self.log(
                    f"SELL EXECUTED: Price: {order.executed.price:.2f}, Size:"
                    f" {order.executed.size}, Cost: {order.executed.value:.2f}, Comm:"
                    f" {order.executed.comm:.2f}"
                )
                self.order_price = order.executed.price
                self.position_size = order.executed.size
                # Set stop loss and take profit
                self.set_exit_orders(order.executed.price, is_buy=False)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order Canceled/Margin/Rejected: {order.status}")

        # Reset order variables
        if order == self.buy_order:
            self.buy_order = None
        elif order == self.sell_order:
            self.sell_order = None
        elif order == self.stop_loss:
            self.stop_loss = None
        elif order == self.take_profit:
            self.take_profit = None

    def notify_trade(self, trade):
        """Track completed trades

        :param trade:

        """
        if not trade.isclosed:
            return

        self.trade_count += 1

        # Track win/loss
        if trade.pnlcomm > 0:
            self.winning_trades += 1
        elif trade.pnlcomm < 0:
            self.losing_trades += 1

        self.log(
            f"TRADE COMPLETED: PnL: Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}"
        )

    def set_exit_orders(self, entry_price, is_buy=True):
        """Set stop loss and take profit orders

        :param entry_price:
        :param is_buy:  (Default value = True)

        """
        # Cancel existing exit orders
        self.cancel_exit_orders()

        atr_val = self.atr[0]

        if is_buy:
            # Stop loss for long position
            stop_price = entry_price - (atr_val * self.p.atr_multiplier)
            risk_amount = entry_price - stop_price

            # Take profit at either channel top or risk*reward ratio, whichever
            # is closer
            target_distance = risk_amount * self.p.tp_ratio
            channel_target = self.channel_top
            # Choose the closer of the two targets
            if abs(channel_target - entry_price) < target_distance:
                profit_target = channel_target
            else:
                profit_target = entry_price + target_distance

            self.stop_loss = self.sell(
                exectype=bt.Order.Stop,
                price=stop_price,
                size=self.position_size,
            )
            self.take_profit = self.sell(
                exectype=bt.Order.Limit,
                price=profit_target,
                size=self.position_size,
            )

            self.log(
                f"Long position: Entry at {entry_price:.2f}, Stop at {stop_price:.2f},"
                f" Target at {profit_target:.2f}"
            )
            self.log(
                f"Risk: {risk_amount:.2f}, Target: {profit_target - entry_price:.2f},"
                f" R:R: {(profit_target - entry_price) / risk_amount:.2f}",
                level="debug",
            )
        else:
            # Stop loss for short position
            stop_price = entry_price + (atr_val * self.p.atr_multiplier)
            risk_amount = stop_price - entry_price

            # Take profit at either channel bottom or risk*reward ratio,
            # whichever is closer
            target_distance = risk_amount * self.p.tp_ratio
            channel_target = self.channel_bottom
            # Choose the closer of the two targets
            if abs(entry_price - channel_target) < target_distance:
                profit_target = channel_target
            else:
                profit_target = entry_price - target_distance

            self.stop_loss = self.buy(
                exectype=bt.Order.Stop,
                price=stop_price,
                size=self.position_size,
            )
            self.take_profit = self.buy(
                exectype=bt.Order.Limit,
                price=profit_target,
                size=self.position_size,
            )

            self.log(
                f"Short position: Entry at {entry_price:.2f}, Stop at {stop_price:.2f},"
                f" Target at {profit_target:.2f}"
            )
            self.log(
                f"Risk: {risk_amount:.2f}, Target: {entry_price - profit_target:.2f},"
                f" R:R: {(entry_price - profit_target) / risk_amount:.2f}",
                level="debug",
            )

    def cancel_exit_orders(self):
        """Cancel stop loss and take profit orders"""
        if self.stop_loss is not None:
            self.cancel(self.stop_loss)
            self.stop_loss = None

        if self.take_profit is not None:
            self.cancel(self.take_profit)
            self.take_profit = None

    def calculate_position_size(self, stop_price):
        """Calculate position size based on risk percentage

        :param stop_price:

        """
        risk_amount = self.broker.getvalue() * (self.p.risk_percent / 100)
        price = self.dataclose[0]
        risk_per_share = abs(price - stop_price)

        if risk_per_share > 0:
            size = risk_amount / risk_per_share
            return int(size)
        return 1  # Default to 1 if calculation fails

    def next(self):
        """Main strategy logic - called for each new price bar"""
        # Update channel values
        self.channel_top = self.upper_line[0]
        self.channel_bottom = self.lower_line[0]

        # Don't trade if any order is pending
        if self.buy_order or self.sell_order:
            return

        # Calculate the threshold zones within the channel
        channel_size = self.channel_top - self.channel_bottom
        upper_threshold = self.channel_top - (channel_size * self.p.channel_pct)
        lower_threshold = self.channel_bottom + (channel_size * self.p.channel_pct)

        # Current price
        price = self.dataclose[0]

        # Print debug information every 10 bars
        if len(self) % 10 == 0:
            self.log(
                f"DEBUG - Close: {price:.2f}, Channel: {self.channel_bottom:.2f} to"
                f" {self.channel_top:.2f}, "
                + f"Width: {channel_size:.2f}, ATR: {self.atr[0]:.2f}",
                level="debug",
            )

            # Check if we're near entry conditions
            if self.dataclose[-1] <= lower_threshold:
                self.log(
                    f"NEAR BUY ZONE - Close: {price:.2f} near lower threshold:"
                    f" {lower_threshold:.2f}",
                    level="debug",
                )
            elif self.dataclose[-1] >= upper_threshold:
                self.log(
                    f"NEAR SELL ZONE - Close: {price:.2f} near upper threshold:"
                    f" {upper_threshold:.2f}",
                    level="debug",
                )

        # If we have no position
        if not self.position:
            # Buy signal: price rebounds from lower channel
            # Criteria: Previous close was at/below lower threshold AND current
            # close > open (bullish candle)
            if self.dataclose[-1] <= lower_threshold and price > self.dataopen[0]:
                # Calculate position size based on risk
                stop_price = self.channel_bottom - self.atr[0]
                size = self.calculate_position_size(stop_price)

                self.log(
                    f"BUY SIGNAL: Price: {price:.2f}, Lower Threshold:"
                    f" {lower_threshold:.2f}, Channel Bottom: {self.channel_bottom:.2f}"
                )
                self.log(
                    f"ORDER DETAILS: Size: {size}, Stop: {stop_price:.2f}, Risk:"
                    f" {(price - stop_price) * size:.2f}"
                )

                self.buy_order = self.buy(size=size)

            # Sell signal: price rebounds from upper channel
            # Criteria: Previous close was at/above upper threshold AND current
            # close < open (bearish candle)
            elif self.dataclose[-1] >= upper_threshold and price < self.dataopen[0]:
                # Calculate position size based on risk
                stop_price = self.channel_top + self.atr[0]
                size = self.calculate_position_size(stop_price)

                self.log(
                    f"SELL SIGNAL: Price: {price:.2f}, Upper Threshold:"
                    f" {upper_threshold:.2f}, Channel Top: {self.channel_top:.2f}"
                )
                self.log(
                    f"ORDER DETAILS: Size: {size}, Stop: {stop_price:.2f}, Risk:"
                    f" {(stop_price - price) * size:.2f}"
                )

                self.sell_order = self.sell(size=size)

        # If we are in a position, update trailing stops
        elif self.position.size > 0:  # Long position
            # Trail stop loss once enough profit is made
            current_profit_pct = (price - self.order_price) / self.order_price * 100

            if current_profit_pct > self.p.trail_percent:
                # Update the stop loss to lock in some profit
                new_stop = price - (
                    self.atr[0] * self.p.trail_atr_mult
                )  # Tighter stop when in profit

                # Only move stop loss up, never down
                if self.stop_loss is not None and new_stop > self.stop_loss.price:
                    self.cancel(self.stop_loss)
                    self.stop_loss = self.sell(
                        exectype=bt.Order.Stop,
                        price=new_stop,
                        size=self.position.size,
                    )
                    self.log(
                        f"Updated trailing stop to {new_stop:.2f} (Profit:"
                        f" {current_profit_pct:.1f}%)"
                    )

        elif self.position.size < 0:  # Short position
            # Trail stop loss once enough profit is made
            current_profit_pct = (self.order_price - price) / self.order_price * 100

            if current_profit_pct > self.p.trail_percent:
                # Update the stop loss to lock in some profit
                new_stop = price + (
                    self.atr[0] * self.p.trail_atr_mult
                )  # Tighter stop when in profit

                # Only move stop loss down, never up
                if self.stop_loss is not None and new_stop < self.stop_loss.price:
                    self.cancel(self.stop_loss)
                    self.stop_loss = self.buy(
                        exectype=bt.Order.Stop,
                        price=new_stop,
                        size=abs(self.position.size),
                    )
                    self.log(
                        f"Updated trailing stop to {new_stop:.2f} (Profit:"
                        f" {current_profit_pct:.1f}%)"
                    )

    def stop(self):
        """Called when backtest is finished"""
        self.log(f"Final Portfolio Value: {self.broker.getvalue():.2f}")

        # Calculate and log statistics
        if self.trade_count > 0:
            win_rate = (self.winning_trades / self.trade_count) * 100
            self.log(
                f"Trade Statistics: {self.trade_count} trades, {win_rate:.2f}% win rate"
            )
        else:
            self.log("No trades executed during the backtest period")

        # Extra information about strategy settings
        self.log(
            f"Strategy Settings: Channel({self.p.period}, {self.p.channel_pct}), "
            + f"ATR({self.p.atr_period}, {self.p.atr_multiplier}), Risk:"
            f" {self.p.risk_percent}%"
        )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Price Channel Trading Strategy",
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
        "--todate",
        "-t",
        default="2024-12-31",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--cash", "-c", default=100000.0, type=float, help="Starting cash"
    )

    # Channel parameters
    parser.add_argument(
        "--period",
        "-p",
        default=20,
        type=int,
        help="Period for channel calculation",
    )

    parser.add_argument(
        "--devfactor",
        "-df",
        default=2.0,
        type=float,
        help="Deviation factor for channel width",
    )

    parser.add_argument(
        "--channel-pct",
        "-cp",
        default=0.3,
        type=float,
        help="How far into channel (0-1) price should reach before signal",
    )

    parser.add_argument(
        "--smooth-period",
        "-sp",
        default=3,
        type=int,
        help="EMA period for smoothing channel boundaries",
    )

    # ATR parameters
    parser.add_argument(
        "--atr-period",
        "-ap",
        default=14,
        type=int,
        help="ATR calculation period",
    )

    parser.add_argument(
        "--atr-multiplier",
        "-am",
        default=2.0,
        type=float,
        help="ATR multiplier for stop-loss distance",
    )

    # Risk management parameters
    parser.add_argument(
        "--risk-percent",
        "-rp",
        default=2.0,
        type=float,
        help="Risk per trade as percentage of portfolio",
    )

    parser.add_argument(
        "--trail-percent",
        "-tp",
        default=50.0,
        type=float,
        help="Percentage of profit at which to start trailing stop",
    )

    parser.add_argument(
        "--trail-atr-mult",
        "-tam",
        default=1.5,
        type=float,
        help="ATR multiplier for trailing stop after activation",
    )

    parser.add_argument(
        "--tp-ratio",
        "-tpr",
        default=2.0,
        type=float,
        help="Target profit to risk ratio for take-profit level",
    )

    # Backtesting options
    parser.add_argument(
        "--plot",
        "-pl",
        action="store_true",
        help="Generate and show a plot of the trading activity",
    )

    parser.add_argument(
        "--debug",
        "-db",
        action="store_true",
        help="Enable detailed debug logging of entry/exit decisions",
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

    # Set log level
    log_level = "debug" if args.debug else "info"

    # Add the strategy
    cerebro.addstrategy(
        ChannelStrategy,
        # Channel parameters
        period=args.period,
        devfactor=args.devfactor,
        channel_pct=args.channel_pct,
        smooth_period=args.smooth_period,
        # ATR parameters
        atr_period=args.atr_period,
        atr_multiplier=args.atr_multiplier,
        # Risk management
        risk_percent=args.risk_percent,
        trail_percent=args.trail_percent,
        trail_atr_mult=args.trail_atr_mult,
        tp_ratio=args.tp_ratio,
        # Logging
        log_level=log_level,
    )

    # Set our desired cash start
    cerebro.broker.setcash(args.cash)

    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Set slippage to 0 (as required for consistent backtesting)
    cerebro.broker.set_slippage_perc(0.0)

    # Add standard analyzers
    add_standard_analyzers(cerebro)

    # Print out the starting conditions
    print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())

    # Print strategy configuration
    print("\nStrategy Configuration:")
    print(f"- Data Source: PostgreSQL database ({args.dbname})")
    print(f"- Symbol: {args.data}")
    print(f"- Date Range: {args.fromdate} to {args.todate}")
    print(
        f"- Channel Parameters: Period={args.period}, Zone={args.channel_pct * 100:.0f}%"
        " from boundary"
    )
    print(
        f"- Risk Management: {args.risk_percent}% per trade, Trail at"
        f" {args.trail_percent}% profit"
    )
    print(
        f"- Stop Loss: {args.atr_multiplier}x ATR({args.atr_period}), Trailing Stop:"
        f" {args.trail_atr_mult}x ATR"
    )
    print(f"- Target Profit Ratio: {args.tp_ratio:.1f}x risk")

    print("\n--- Starting Backtest ---\n")

    # Run the strategy
    results = cerebro.run()
    strat = results[0]

    # Print out final results
    print("\n--- Backtest Results ---\n")
    print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())

    # Get analyzer results
    try:
        returns = strat.analyzers.returns.get_analysis()
        total_return = returns.get("rtot", 0) * 100
        if total_return is not None:
            print(f"Return: {total_return:.2f}%")
        else:
            print("Return: N/A")
    except Exception as e:
        print(f"Unable to calculate return: {e}")

    try:
        sharpe = strat.analyzers.sharperatio.get_analysis()
        sharpe_ratio = sharpe.get("sharperatio", 0)
        if sharpe_ratio is not None:
            print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
        else:
            print("Sharpe Ratio: N/A")
    except Exception as e:
        print(f"Unable to calculate Sharpe ratio: {e}")

    try:
        drawdown = strat.analyzers.drawdown.get_analysis()
        max_dd = drawdown.get("max", {}).get("drawdown", 0)
        if max_dd is not None:
            print(f"Max Drawdown: {max_dd:.2f}%")
        else:
            print("Max Drawdown: N/A")
    except Exception as e:
        print(f"Unable to calculate Max Drawdown: {e}")

    try:
        trades = strat.analyzers.trades.get_analysis()
        total_trades = trades.get("total", {}).get("total", 0)

        if total_trades > 0:
            won_trades = trades.get("won", {}).get("total", 0)
            lost_trades = trades.get("lost", {}).get("total", 0)
            win_rate = won_trades / total_trades * 100 if total_trades > 0 else 0

            print(f"Total Trades: {total_trades}")
            print(f"Won Trades: {won_trades}")
            print(f"Lost Trades: {lost_trades}")
            print(f"Win Rate: {win_rate:.2f}%")

            # Additional trade metrics
            avg_win = trades.get("won", {}).get("pnl", {}).get("average", 0)
            avg_loss = trades.get("lost", {}).get("pnl", {}).get("average", 0)

            if avg_win is not None and avg_loss is not None and avg_loss != 0:
                profit_factor = (
                    abs(avg_win * won_trades / (avg_loss * lost_trades))
                    if lost_trades > 0
                    else float("inf")
                )
                print(f"Avg Win: {avg_win:.2f}")
                print(f"Avg Loss: {avg_loss:.2f}")
                print(f"Profit Factor: {profit_factor:.2f}")
        else:
            print("No trades executed during the backtest period")
    except Exception as e:
        print(f"Unable to calculate trade statistics: {e}")

    # Plot if requested
    if args.plot:
        try:
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
        except Exception as e:
            print(f"Error creating plot: {e}")


if __name__ == "__main__":
    main()
