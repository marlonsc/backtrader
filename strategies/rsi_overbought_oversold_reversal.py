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
RSI OVERBOUGHT/OVERSOLD REVERSAL STRATEGY WITH POSTGRESQL DATABASE - (rsi-reversal)
===============================================================================

This strategy implements a mean reversion system based on RSI (Relative Strength Index)
extremes. It looks for overbought and oversold conditions to identify potential
price reversals.

STRATEGY LOGIC:
--------------
1. Oversold Condition (Buy Signal):
   - RSI falls below oversold threshold (default: 30)
   - Wait for RSI to start moving back up (confirmation)
   - Enter long position

2. Overbought Condition (Sell Signal):
   - RSI rises above overbought threshold (default: 70)
   - Wait for RSI to start moving back down (confirmation)
   - Exit long position

3. Optional Confirmation Indicators:
   - Support/Resistance levels
   - Price action (candlestick patterns)
   - Stochastic Oscillator crossovers

MARKET CONDITIONS:
----------------
!!! WARNING: THIS STRATEGY IS SPECIFICALLY DESIGNED FOR SIDEWAYS/RANGING MARKETS ONLY !!!

- PERFORMS BEST: In markets with clear overbought and oversold levels that oscillate between
  support and resistance zones. The strategy needs price to regularly return to the mean.

- AVOID USING: During strong trending markets where RSI can remain overbought/oversold for
  extended periods without reverting. Using this strategy in trending markets will lead to
  multiple false signals and poor performance.

- IDEAL TIMEFRAMES: 1-hour, 4-hour, and daily charts for stocks that exhibit range-bound behavior

- OPTIMAL MARKET CONDITION: Range-bound markets with clear support and resistance levels and
  limited breakouts. Stocks with beta near 1.0 and low ADX readings (below 25) typically work best.

The strategy will struggle in strong trends as RSI can remain in extreme territories,
resulting in premature exit signals or false entry signals. It performs best when
price oscillates within a defined range, allowing RSI to regularly move between
overbought and oversold zones.

PARAMETERS ADJUSTMENT:
--------------------
- For wider ranges: Increase RSI thresholds (e.g., 25/75)
- For narrow ranges: Decrease RSI thresholds (e.g., 35/65)
- For stronger trends: Increase confirmation bars (3+)
- For quicker signals: Decrease confirmation bars (1)

OPTIMIZED FOR:
-------------
- Timeframe: 1-hour data
- Year: 2024
- Market: Stocks showing mean reversion tendencies
- Best Performance: Sideways and ranging markets

USAGE:
------
python strategies/rsi_overbought_oversold_reversal.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

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

RSI PARAMETERS:
--------------
--rsi-period, -rp     : Period for RSI calculation (default: 14)
--oversold, -os       : Oversold threshold for RSI (default: 30)
--overbought, -ob     : Overbought threshold for RSI (default: 70)
--confirmation, -cf   : Number of bars for confirmation (default: 2)

STOCHASTIC PARAMETERS:
--------------------
--use-stoch, -us     : Use Stochastic Oscillator for confirmation (default: False)
--stoch-period, -sp  : Period for Stochastic calculation (default: 14)
--stoch-smooth, -ss  : Smoothing period for Stochastic (default: 3)

EXIT PARAMETERS:
---------------
--use-stop, -us     : Use stop loss (default: True)
--stop-pct, -sp     : Stop loss percentage (default: 2.0)
--use-trail, -ut    : Enable trailing stop loss (default: False)
--trail-pct, -tp    : Trailing stop percentage (default: 1.0)
--take-profit, -tkp  : Take profit percentage (default: 4.0)

POSITION SIZING:
---------------
--risk-percent, -rp  : Percentage of equity to risk per trade (default: 1.0)
--max-position, -mp  : Maximum position size as percentage of equity (default: 20.0)

TRADE THROTTLING:
---------------
--trade-throttle-days, -ttd : Minimum days between trades (default: 1)

OTHER:
-----
--plot, -p          : Generate and show a plot of the trading activity

EXAMPLE:
--------
python strategies/rsi_overbought_oversold_reversal.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --rsi-period 14 --oversold 30 --overbought 70 --plot
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import datetime
import os
import sys
import pandas as pd
import backtrader as bt

# Import utility functions
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
        ("datetime", None),
        ("open", "Open"),
        ("high", "High"),
        ("low", "Low"),
        ("close", "Close"),
        ("volume", "Volume"),
        ("openinterest", None),
    )


class RSIOverboughtOversoldStrategy(bt.Strategy, TradeThrottling):
    """
    RSI Overbought/Oversold Reversal Strategy

    This strategy looks for extreme RSI values to identify potential reversals:
    - Buy when RSI moves below oversold level and starts to turn up
    - Sell when RSI moves above overbought level and starts to turn down
    - Optional confirmation using Stochastic Oscillator

    !!! IMPORTANT MARKET CONDITION WARNING !!!

    This strategy is SPECIFICALLY DESIGNED for SIDEWAYS/RANGING MARKETS ONLY.
    It performs POORLY in trending markets where RSI can remain in extreme territories
    for extended periods without reverting.

    BEST MARKET CONDITIONS:
    - Stocks trading in defined ranges with clear support and resistance
    - Low ADX readings (below 25) indicating absence of strong trends
    - Markets with regular mean reversion behavior
    - Periods of low to moderate volatility

    AVOID USING IN:
    - Strong bull or bear markets with persistent trends
    - Breakout situations or after significant news events
    - Stocks with high momentum characteristics
    - High volatility environments

    Using this strategy in trending markets will result in numerous false signals,
    premature exits, and poor overall performance.
    """

    params = (
        # RSI parameters
        ("rsi_period", 14),  # Period for RSI calculation
        ("oversold", 30),  # Oversold threshold for RSI
        ("overbought", 70),  # Overbought threshold for RSI
        ("confirmation", 2),  # Number of bars for confirmation
        # Stochastic parameters
        ("use_stoch", False),  # Use stochastic for confirmation
        ("stoch_period", 14),  # Period for stochastic
        ("stoch_smooth", 3),  # Smoothing period for stochastic
        # Order size parameters
        ("risk_percent", 1.0),  # Percentage of equity to risk per trade
        ("max_position", 20.0),  # Maximum position size as percentage
        # Stop parameters
        ("stop_pct", 2.0),  # Stop loss percentage
        ("trail_stop", False),  # Use trailing stop
        ("trail_percent", 2.0),  # Trailing stop percentage
        # Trade throttling
        ("trade_throttle_days", 5),  # Minimum days between trades
        # Debug and logging
        ("logging_level", "info"),  # Logging level: debug, info, warning, error
    )

    def log(self, txt, dt=None, level="info"):
        """Logging function"""
        if level == "debug" and self.p.logging_level != "debug":
            return

        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}: {txt}")

    def __init__(self):
        # Keep track of price data
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # Create RSI indicator
        self.rsi = bt.indicators.RSI(
            self.dataclose, period=self.p.rsi_period, plotname="RSI"
        )

        # Create Stochastic indicator if enabled
        if self.p.use_stoch:
            self.stoch = bt.indicators.Stochastic(
                self.data,
                period=self.p.stoch_period,
                period_dfast=self.p.stoch_smooth,
                plotname="Stochastic",
            )

        # Trading state variables
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.stop_price = None
        self.take_profit_price = None
        self.trail_price = None
        self.highest_price = None

        # Confirmation state variables
        self.buy_signal_count = 0
        self.sell_signal_count = 0
        self.last_rsi = None

        # For trade throttling
        self.last_trade_date = None

    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED: Price: {order.executed.price:.2f}, "
                    f"Size: {order.executed.size}, Cost: {order.executed.value:.2f}, "
                    f"Comm: {order.executed.comm:.2f}"
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm

                # Set stop loss and take profit prices
                if self.p.use_stop:
                    self.stop_price = self.buyprice * (1 - self.p.stop_pct / 100)
                    self.log(f"Stop loss set at {self.stop_price:.2f}")

                self.take_profit_price = self.buyprice * (1 + self.p.take_profit / 100)
                self.log(f"Take profit set at {self.take_profit_price:.2f}")

                self.highest_price = self.buyprice

                # Set initial trailing stop price if enabled
                if self.p.use_trail:
                    self.trail_price = self.buyprice * (1 - self.p.trail_pct / 100)
                    self.log(f"Initial trailing stop set at {self.trail_price:.2f}")

                # Reset confirmation counters
                self.buy_signal_count = 0
                self.sell_signal_count = 0

                # Update last trade date for throttling
                self.last_trade_date = self.datas[0].datetime.date(0)

            else:
                self.log(
                    f"SELL EXECUTED: Price: {order.executed.price:.2f}, "
                    f"Size: {order.executed.size}, Cost: {order.executed.value:.2f}, "
                    f"Comm: {order.executed.comm:.2f}"
                )

                # Reset stops and confirmation counters
                self.stop_price = None
                self.trail_price = None
                self.take_profit_price = None
                self.buy_signal_count = 0
                self.sell_signal_count = 0

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order Canceled/Margin/Rejected: {order.status}")

        self.order = None

    def notify_trade(self, trade):
        """Track completed trades"""
        if not trade.isclosed:
            return

        self.log(
            f"TRADE COMPLETED: PnL: Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}"
        )

    def calculate_position_size(self):
        """Calculate position size based on risk percentage"""
        available_cash = self.broker.getcash()
        portfolio_value = self.broker.getvalue()
        current_price = self.dataclose[0]

        # Calculate position size based on risk percentage
        risk_amount = portfolio_value * (self.p.risk_percent / 100)
        price_risk = current_price * (self.p.stop_pct / 100)

        if price_risk > 0:
            size = int(risk_amount / price_risk)
        else:
            # Fallback to fixed percentage
            size = int(available_cash * (self.p.max_position / 100) / current_price)

        # Ensure we don't exceed maximum position size
        max_size = int(available_cash * (self.p.max_position / 100) / current_price)
        return min(size, max_size)

    def is_rsi_valid(self):
        """Check if RSI has enough data to be valid"""
        # RSI needs at least period+1 data points to be valid
        return len(self) > self.p.rsi_period

    def is_stoch_valid(self):
        """Check if Stochastic has enough data to be valid"""
        # Stochastic needs at least period+K period data points to be valid
        min_bars = max(self.p.stoch_period, self.p.stoch_smooth)
        return len(self) > min_bars

    def should_buy(self):
        """Check if we should enter a long position"""
        # Need enough bars for all indicators
        if not self.is_rsi_valid():
            return False

        # Need at least 2 bars of RSI data to check for a turn
        if len(self) <= self.p.rsi_period + 1:
            return False

        # Check if market is in a strong trend (avoid if it is)
        # This helps ensure we're in a ranging market which is optimal for this strategy
        adx = bt.indicators.AverageDirectionalMovementIndex(self.data, period=14)
        if adx > 25:  # ADX > 25 indicates a trending market
            self.log("Market appears to be trending, avoiding entry", level="warning")
            return False

        # Check if RSI is below oversold and turning up
        rsi_below_oversold = self.rsi[0] < self.p.oversold
        rsi_turning_up = self.rsi[0] > self.rsi[-1]

        # Count how many bars RSI has been below oversold
        oversold_bars = 0
        for i in range(self.p.confirmation):
            if i + 1 < len(self.rsi) and self.rsi[-i - 1] < self.p.oversold:
                oversold_bars += 1

        if (
            rsi_below_oversold
            and rsi_turning_up
            and oversold_bars >= self.p.confirmation
        ):
            # Basic RSI signal is valid
            self.log(f"RSI oversold signal detected: {self.rsi[0]:.2f}", level="debug")

            # Check additional stochastic confirmation if enabled
            if self.p.use_stoch and not self.is_stoch_valid():
                self.log("Stochastic confirmation not valid", level="debug")
                return False

            if self.p.use_stoch:
                # Check if stochastic is in oversold zone and turning up
                stoch_oversold = self.stoch.percK[0] < 20 and self.stoch.percD[0] < 20
                stoch_turning_up = (
                    self.stoch.percK[0] > self.stoch.percK[-1]
                    and self.stoch.percD[0] > self.stoch.percD[-1]
                )

                if stoch_oversold and stoch_turning_up:
                    self.log("Stochastic confirms oversold condition", level="debug")
                    return True
                else:
                    self.log("Stochastic doesn't confirm signal", level="debug")
                    return False
            else:
                return True  # RSI signal only

        return False

    def should_sell(self):
        """Check if we should exit the position"""
        # Check stop loss
        if (
            self.p.use_stop
            and self.stop_price is not None
            and self.datalow[0] <= self.stop_price
        ):
            self.log(
                f"STOP LOSS TRIGGERED: Price: {self.datalow[0]:.2f}, Stop:"
                f" {self.stop_price:.2f}"
            )
            return True

        # Check take profit
        if (
            self.take_profit_price is not None
            and self.datahigh[0] >= self.take_profit_price
        ):
            self.log(
                f"TAKE PROFIT REACHED: Price: {self.datahigh[0]:.2f}, Target:"
                f" {self.take_profit_price:.2f}"
            )
            return True

        # Update trailing stop if enabled
        if (
            self.p.use_trail
            and self.trail_price is not None
            and self.datahigh[0] > self.highest_price
        ):
            self.highest_price = self.datahigh[0]
            self.trail_price = self.highest_price * (1 - self.p.trail_pct / 100)
            self.log(f"Updated trailing stop to {self.trail_price:.2f}", level="debug")

        # Check trailing stop
        if (
            self.p.use_trail
            and self.trail_price is not None
            and self.datalow[0] <= self.trail_price
        ):
            self.log(
                f"TRAILING STOP TRIGGERED: Price: {self.datalow[0]:.2f}, Stop:"
                f" {self.trail_price:.2f}"
            )
            return True

        # Check if indicators have enough data to be valid
        if not self.is_rsi_valid():
            return False

        # Check for overbought RSI
        if self.rsi[0] >= self.p.overbought:
            if self.rsi[0] <= self.rsi[-1]:  # RSI starting to turn down
                self.sell_signal_count += 1
                if self.sell_signal_count >= self.p.confirmation:
                    self.log(
                        f"RSI OVERBOUGHT SIGNAL: RSI: {self.rsi[0]:.2f}, Price:"
                        f" {self.dataclose[0]:.2f}"
                    )
                    return True
        else:
            self.sell_signal_count = 0  # Reset counter if not overbought

        # Additional confirmation using Stochastic if enabled
        if self.p.use_stoch and self.is_stoch_valid():
            if self.stoch.lines.percK[0] >= 80:  # Stochastic overbought
                if (
                    self.stoch.lines.percK[0] < self.stoch.lines.percK[-1]
                ):  # Starting to turn down
                    self.log(
                        "STOCHASTIC OVERBOUGHT SIGNAL: K:"
                        f" {self.stoch.lines.percK[0]:.2f}, D:"
                        f" {self.stoch.lines.percD[0]:.2f}"
                    )
                    return True

        return False

    def next(self):
        # If an order is pending, we cannot send a new one
        if self.order:
            return

        # Store the current RSI value for reference
        if self.is_rsi_valid():
            self.last_rsi = self.rsi[0]

        # Debug info every 5 bars
        if len(self) % 5 == 0:
            rsi_msg = (
                f"RSI: {self.rsi[0]:.2f}"
                if self.is_rsi_valid()
                else "RSI: Initializing"
            )
            self.log(f"Close: {self.dataclose[0]:.2f}, {rsi_msg}", level="debug")
            if self.p.use_stoch and self.is_stoch_valid():
                self.log(
                    f"Stochastic K: {self.stoch.lines.percK[0]:.2f}, "
                    f"D: {self.stoch.lines.percD[0]:.2f}",
                    level="debug",
                )

        # Check if we are in the market
        if not self.position:
            # Check for buy signal
            if self.should_buy():
                # Check if we can trade now (trade throttling)
                if not self.can_trade_now():
                    self.log(
                        "TRADE THROTTLED: Need to wait"
                        f" {self.p.trade_throttle_days} days between trades",
                        level="debug",
                    )
                    return

                size = self.calculate_position_size()
                if size > 0:
                    self.log(
                        f"BUY CREATE: Price: {self.dataclose[0]:.2f}, Size: {size},"
                        f" RSI: {self.rsi[0]:.2f}"
                    )
                    self.order = self.buy(size=size)

        else:
            # Check for sell signal
            if self.should_sell():
                self.log(
                    f"SELL CREATE: Price: {self.dataclose[0]:.2f}, RSI:"
                    f" {self.rsi[0]:.2f}"
                )
                self.order = self.sell(size=self.position.size)

    def stop(self):
        """Called when backtest is complete"""
        self.log("RSI Overbought/Oversold Reversal Strategy completed")
        self.log(f"Final Portfolio Value: {self.broker.getvalue():.2f}")

        # Add a note about market conditions
        self.log(
            "NOTE: This strategy is specifically designed for SIDEWAYS/RANGING MARKETS"
        )
        self.log(
            "      It performs poorly in strong trending markets where RSI remains"
            " extreme"
        )
        self.log(
            "      Ideal conditions: Price oscillating between support and resistance"
            " levels"
        )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=(
            "RSI Overbought/Oversold Reversal Strategy for Sideways/Ranging Markets"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Basic parameters
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
        "--cash", "-c", type=float, default=100000.0, help="Starting cash"
    )

    # RSI parameters
    parser.add_argument(
        "--rsi-period", "-rp", type=int, default=14, help="Period for RSI calculation"
    )
    parser.add_argument(
        "--oversold", "-os", type=float, default=30, help="Oversold threshold for RSI"
    )
    parser.add_argument(
        "--overbought",
        "-ob",
        type=float,
        default=70,
        help="Overbought threshold for RSI",
    )
    parser.add_argument(
        "--confirmation",
        "-cf",
        type=int,
        default=2,
        help="Number of bars for confirmation",
    )

    # Stochastic parameters
    parser.add_argument(
        "--use-stoch",
        "-us",
        action="store_true",
        help="Use Stochastic Oscillator for confirmation",
    )
    parser.add_argument(
        "--stoch-period",
        "-sp",
        type=int,
        default=14,
        help="Period for Stochastic calculation",
    )
    parser.add_argument(
        "--stoch-smooth",
        "-ss",
        type=int,
        default=3,
        help="Smoothing period for Stochastic",
    )

    # Exit parameters
    parser.add_argument("--use-stop", "-st", action="store_true", help="Use stop loss")
    parser.add_argument(
        "--stop-pct", "-sp", type=float, default=2.0, help="Stop loss percentage"
    )
    parser.add_argument(
        "--use-trail", "-ut", action="store_true", help="Enable trailing stop loss"
    )
    parser.add_argument(
        "--trail-pct", "-tp", type=float, default=1.0, help="Trailing stop percentage"
    )
    parser.add_argument(
        "--take-profit", "-tkp", type=float, default=4.0, help="Take profit percentage"
    )

    # Position sizing parameters
    parser.add_argument(
        "--risk-percent",
        "-rp",
        type=float,
        default=1.0,
        help="Percentage of equity to risk per trade",
    )
    parser.add_argument(
        "--max-position",
        "-mp",
        type=float,
        default=20.0,
        help="Maximum position size as percentage of equity",
    )

    # Trade throttling
    parser.add_argument(
        "--trade-throttle-days",
        "-ttd",
        type=int,
        default=1,
        help="Minimum days between trades",
    )

    # Other parameters
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

    # Add the data feed
    cerebro.adddata(data)

    # Add strategy
    cerebro.addstrategy(
        RSIOverboughtOversoldStrategy,
        # RSI parameters
        rsi_period=args.rsi_period,
        oversold=args.oversold,
        overbought=args.overbought,
        confirmation=args.confirmation,
        # Stochastic parameters
        use_stoch=args.use_stoch,
        stoch_period=args.stoch_period,
        stoch_smooth=args.stoch_smooth,
        # Exit parameters
        use_stop=args.use_stop,
        stop_pct=args.stop_pct,
        use_trail=args.use_trail,
        trail_pct=args.trail_pct,
        take_profit=args.take_profit,
        # Position sizing parameters
        risk_percent=args.risk_percent,
        max_position=args.max_position,
        # Trade throttling
        trade_throttle_days=args.trade_throttle_days,
        # Logging
        logging_level="info",
    )

    # Add standard analyzers
    add_standard_analyzers(cerebro)

    # Set cash
    cerebro.broker.setcash(args.cash)

    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)

    # Set slippage
    cerebro.broker.set_slippage_perc(0.0)

    # Print out the starting conditions
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Print strategy configuration
    print("\nStrategy Configuration:")
    print(f"Symbol: {args.data}")
    print(f"Date Range: {args.fromdate} to {args.todate}")
    print(
        f"RSI Parameters: Period={args.rsi_period}, Oversold={args.oversold},"
        f" Overbought={args.overbought}"
    )
    print(f"Confirmation Bars: {args.confirmation}")

    if args.use_stoch:
        print(
            f"Using Stochastic ({args.stoch_period}/{args.stoch_smooth}) for"
            " confirmation"
        )

    print("\nExit Parameters:")
    if args.use_stop:
        print(f"Stop Loss: {args.stop_pct}%")
    else:
        print("Stop Loss: Disabled")

    if args.use_trail:
        print(f"Trailing Stop: {args.trail_pct}%")
    else:
        print("Trailing Stop: Disabled")

    print(f"Take Profit: {args.take_profit}%")

    print(
        f"\nPosition Sizing: {args.risk_percent}% risk per trade (max"
        f" {args.max_position}%)"
    )

    if args.trade_throttle_days > 0:
        print(f"Trade Throttling: {args.trade_throttle_days} days between trades")

    print("\n--- Starting Backtest ---\n")
    print(
        "*** IMPORTANT: This strategy is specifically designed for SIDEWAYS/RANGING"
        " MARKETS ***"
    )
    print(
        "It performs poorly in strongly trending markets where RSI can remain in"
        " extreme"
    )
    print(
        "territories for extended periods. Best used in range-bound markets with clear"
    )
    print("support and resistance zones where price regularly oscillates.\n")

    # Run the strategy
    results = cerebro.run()

    # Print final portfolio value
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: ${final_value:.2f}")

    # Use the centralized performance metrics function
    print_performance_metrics(cerebro, results)

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
