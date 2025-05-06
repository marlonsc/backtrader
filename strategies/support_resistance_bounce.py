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
"""BOLLINGER BANDS MEAN REVERSION STRATEGY WITH POSTGRESQL DATABASE - (bb_mean_reversal)
===============================================================================
This strategy is a mean reversion trading system that buys when price touches the
lower Bollinger Band and RSI is oversold, then sells when price touches the upper
Bollinger Band and RSI is overbought. It's designed to capture price movements in
range-bound or sideways markets.
STRATEGY LOGIC:
--------------
- Go LONG when price CLOSES BELOW the LOWER Bollinger Band AND RSI < 30 (oversold)
- Exit LONG when price touches the UPPER Bollinger Band AND RSI is overbought
- Or exit when price crosses the middle band (optional)
- Optional stop-loss below the recent swing low
MARKET CONDITIONS:
----------------
- Best used in SIDEWAYS or RANGE-BOUND markets
- Avoids trending markets where mean reversion is less reliable
- Performs well in consolidation periods with clear support and resistance
BOLLINGER BANDS:
--------------
Bollinger Bands consist of:
- A middle band (typically a 20-period moving average)
- An upper band (middle band + 2 standard deviations)
- A lower band (middle band - 2 standard deviations)
These bands adapt to volatility - widening during volatile periods and
narrowing during less volatile periods.
EXAMPLE COMMANDS:
---------------
1. Standard configuration - classic support/resistance bounce:
python strategies/support_resistance_bounce.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31
2. More sensitive settings - tighter bands for choppy markets:
python strategies/support_resistance_bounce.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --bb-period 15 --bb-dev 1.8
3. Extreme oversold/overbought thresholds - fewer but stronger signals:
python strategies/support_resistance_bounce.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --rsi-oversold 25 --rsi-overbought 75
4. Risk management focus - fixed stop loss with larger position:
python strategies/support_resistance_bounce.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --stop-loss --stop-atr 2.0 --risk-percent 2.0
5. Faster exit approach - use middle band crossing for quicker profits:
python strategies/support_resistance_bounce.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --exit-middle-band
RSI (RELATIVE STRENGTH INDEX):
----------------------------
- Oscillator that measures momentum
- Ranges from 0 to 100
- Values below 30 typically indicate oversold conditions
- Values above 70 typically indicate overbought conditions
USAGE:
------
python strategies/sideways/bb_mean_reversal.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]
REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2024-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2024-12-31)
OPTIONAL ARGUMENTS:
------------------
--dbuser, -u    : PostgreSQL username (default: jason)
--dbpass, -p    : PostgreSQL password (default: fsck)
--dbname, -n    : PostgreSQL database name (default: market_data)
--cash, -c      : Initial cash for the strategy (default: $100,000)
--bb-length, -bl: Period for Bollinger Bands calculation (default: 20)
--bb-mult, -bm  : Multiplier for standard deviation (default: 2.0)
--rsi-period, -rp: Period for RSI calculation (default: 14)
--rsi-oversold, -ro: RSI oversold threshold (default: 30)
--rsi-overbought, -rob: RSI overbought threshold (default: 70)
--exit-middle, -em: Exit when price crosses the middle band (default: False)
--use-stop, -us : Use stop loss (default: False)
--stop-pct, -sp : Stop loss percentage (default: 2.0)
--matype, -mt   : Moving average type for Bollinger Bands basis (default: SMA, options: SMA, EMA, WMA, SMMA)
--plot, -p      : Generate and show a plot of the trading activity
EXAMPLE:
--------
python strategies/support_resistance_bounce.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --exit-middle --use-stop --stop-pct 2.5 --plot"""

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
        ("rsi", "RSI"),  # Column containing the RSI value
        ("openinterest", None),  # Column for open interest (not available)
    )


class BollingerMeanReversionStrategy(bt.Strategy, TradeThrottling):
    """Bollinger Bands Mean Reversion Strategy
This strategy attempts to capture mean reversion moves by:
1. Buying when price touches or crosses below the lower Bollinger Band and RSI < 30
2. Selling when price touches or crosses above the upper Bollinger Band and RSI > 70
Additional exit mechanisms include:
- Optional exit when price crosses the middle Bollinger Band
- Optional stop loss to limit potential losses
** IMPORTANT: This strategy is specifically designed for SIDEWAYS/RANGING MARKETS **
It performs poorly in trending markets where prices can remain overbought or oversold
for extended periods without reverting.
Strategy Logic:
- Buy when price crosses or touches lower Bollinger Band and RSI is oversold
- Sell when price crosses or touches upper Bollinger Band and RSI is overbought
- Uses risk-based position sizing for proper money management
- Implements cool down period to avoid overtrading
Best Market Conditions:
- Sideways or range-bound markets with clear support and resistance
- Markets with regular mean reversion tendencies
- Low ADX readings (below 25) indicating absence of strong trends
- Avoid using in strong trending markets"""

    params = (
        ("position_size", 0.2),  # Percentage of portfolio to use per position
        ("bbands_period", 20),  # Bollinger Bands period
        ("bbands_dev", 2),  # Number of standard deviations
        ("rsi_period", 14),  # RSI period
        ("rsi_buy_threshold", 30),  # RSI threshold for buy signals
        ("rsi_sell_threshold", 70),  # RSI threshold for sell signals
        ("stop_loss_pct", 2.0),  # Stop loss percentage
        ("use_stop_loss", True),  # Whether to use stop loss
        (
            "exit_middle",
            False,
        ),  # Whether to exit when price crosses middle band
        # Risk management parameters
        ("risk_percent", 1.0),  # Percentage of equity to risk per trade
        ("max_position", 20.0),  # Maximum position size as percentage
        # Trade throttling
        ("trade_throttle_days", 5),  # Minimum days between trades
        # Other
        ("log_level", "info"),  # Logging level
    )

    def log(self, txt, dt=None, level="info"):
"""Logging function for the strategy

Args::
    txt: 
    dt: (Default value = None)
    level: (Default value = "info")"""
    level: (Default value = "info")"""
        if level == "debug" and self.p.log_level != "debug":
            return

        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}: {txt}")

    def __init__(self):
""""""
"""Calculate how many shares to buy based on risk-based position sizing

Args::
    price:"""
    price:"""
        available_cash = self.broker.get_cash()
        value = self.broker.getvalue()
        current_price = price

        # Calculate position size based on risk percentage if stop loss is
        # enabled
        if self.p.use_stop_loss:
            # Calculate the risk amount in dollars
            risk_amount = value * (self.p.risk_percent / 100.0)

            # Calculate the stop loss price
            stop_price = current_price * (1.0 - self.p.stop_loss_pct / 100.0)

            # Calculate the risk per share
            risk_per_share = current_price - stop_price

            if risk_per_share > 0:
                # Calculate position size based on risk
                risk_based_size = int(risk_amount / risk_per_share)

                # Calculate size based on fixed percentage of equity
                equity_based_size = int((value * self.p.position_size) / current_price)

                # Use the smaller of the two sizes
                size = min(risk_based_size, equity_based_size)
            else:
                # If risk per share is zero or negative, use equity-based
                # sizing
                size = int((value * self.p.position_size) / current_price)
        else:
            # Fixed percentage of available equity without risk-based
            # calculation
            cash_to_use = value * self.p.position_size

            # Make sure we don't exceed maximum available cash
            max_cash = available_cash * (self.p.max_position / 100.0)
            cash_to_use = min(cash_to_use, max_cash)

            # Calculate number of shares (integer)
            size = int(cash_to_use / current_price)

        return size

    def next(self):
""""""
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

    def notify_order(self, order):
"""Handle order notifications

Args::
    order:"""
    order:"""
        if order.status in [order.Submitted, order.Accepted]:
            # Order pending, do nothing
            return

        # Check if order was completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED: Price: {order.executed.price:.2f}, Size:"
                    f" {order.executed.size}, Cost: {order.executed.value:.2f}, Comm:"
                    f" {order.executed.comm:.2f}"
                )
            else:  # sell
                self.log(
                    f"SELL EXECUTED: Price: {order.executed.price:.2f}, Size:"
                    f" {order.executed.size}, Cost: {order.executed.value:.2f}, Comm:"
                    f" {order.executed.comm:.2f}"
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order Canceled/Margin/Rejected: {order.status}")

        # Reset order status
        self.order = None

    def notify_trade(self, trade):
"""Track completed trades

Args::
    trade:"""
    trade:"""
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


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=(
            "Bollinger Bands Mean Reversion Strategy with RSI (for Sideways Markets)"
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
        choices=["SMA", "EMA", "WMA", "SMMA"],
        help="Moving average type for Bollinger Bands basis",
    )

    # RSI parameters
    parser.add_argument(
        "--rsi-period",
        "-rp",
        default=14,
        type=int,
        help="Period for RSI calculation",
    )

    parser.add_argument(
        "--rsi-oversold",
        "-ro",
        default=30,
        type=int,
        help="RSI oversold threshold (buy signal)",
    )

    parser.add_argument(
        "--rsi-overbought",
        "-rob",
        default=70,
        type=int,
        help="RSI overbought threshold (sell signal)",
    )

    # Exit strategy parameters
    parser.add_argument(
        "--exit-middle",
        "-em",
        action="store_true",
        help="Exit when price crosses the middle band",
    )

    parser.add_argument("--use-stop", "-us", action="store_true", help="Use stop loss")

    parser.add_argument(
        "--stop-pct",
        "-sp",
        default=2.0,
        type=float,
        help="Stop loss percentage from entry",
    )

    # Position sizing parameters
    parser.add_argument(
        "--position-percent",
        "-pp",
        default=20.0,
        type=float,
        help="Percentage of equity to use per trade",
    )

    parser.add_argument(
        "--max-position-percent",
        "-mpp",
        default=20.0,
        type=float,
        help="Maximum position size as percentage of equity",
    )

    parser.add_argument(
        "--risk-percent",
        "-rpct",
        default=1.0,
        type=float,
        help="Percentage of equity to risk per trade",
    )

    # Trade throttling parameters
    parser.add_argument(
        "--trade-throttle-days",
        "-ttd",
        default=5,
        type=int,
        help="Minimum days between trades (0 = no throttling)",
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

    # Add the Bollinger Mean Reversion strategy
    cerebro.addstrategy(
        BollingerMeanReversionStrategy,
        # Bollinger Bands parameters
        bbands_period=args.bb_length,
        bbands_dev=args.bb_mult,
        rsi_period=args.rsi_period,
        rsi_buy_threshold=args.rsi_oversold,
        rsi_sell_threshold=args.rsi_overbought,
        stop_loss_pct=args.stop_pct,
        use_stop_loss=args.use_stop,
        exit_middle=args.exit_middle,
        # Position sizing parameters
        position_size=args.position_percent / 100.0,  # Convert percentage to decimal
        risk_percent=args.risk_percent,  # Use the specified risk percentage
        max_position=args.max_position_percent,
        # Use the specified maximum position size
        # Trade throttling parameters
        # Use the specified trade throttle days
        trade_throttle_days=args.trade_throttle_days,
    )

    # Set our desired cash start
    cerebro.broker.setcash(args.cash)

    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Set slippage to 0 (as required)
    cerebro.broker.set_slippage_perc(0.0)

    # Add standard analyzers
    add_standard_analyzers(cerebro)

    # Print out the starting conditions
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Print strategy configuration
    print("\nStrategy Configuration:")
    print(f"- Data Source: PostgreSQL database ({args.dbname})")
    print(f"- Symbol: {args.data}")
    print(f"- Date Range: {args.fromdate} to {args.todate}")
    print(f"- Entry: Price below lower BB AND RSI < {args.rsi_oversold}")
    print(f"- Exit: Price above upper BB AND RSI > {args.rsi_overbought}")

    if args.exit_middle:
        print("- Additional Exit: Price crosses above middle band")

    if args.use_stop:
        print(f"- Stop Loss: {args.stop_pct}% below entry price")

    print("\n--- Starting Backtest ---\n")

    # Run the strategy
    results = cerebro.run()

    # Print out final results
    print("\n--- Backtest Results ---\n")
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Use the centralized performance metrics function
    print_performance_metrics(cerebro, results)

    # Plot if requested
    if args.plot:
        cerebro.plot(style="candle", barup="green", bardown="red")


if __name__ == "__main__":
    main()
