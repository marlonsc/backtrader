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
MOVING AVERAGE CROSSOVER STRATEGY WITH POSTGRESQL DATABASE - (ma-crossover)
==========================================================================

This strategy implements a trend-following system based on moving average crossovers.
It uses two moving averages (a short-term and a long-term) to generate buy and sell signals.

STRATEGY LOGIC:
--------------
1. Bullish Crossover (Golden Cross):
   - The shorter-term MA crosses above the longer-term MA
   - This is a buy signal

2. Bearish Crossover (Death Cross):
   - The shorter-term MA crosses below the longer-term MA
   - This is a sell signal

MARKET CONDITIONS:
----------------
*** THIS STRATEGY IS SPECIFICALLY DESIGNED FOR TRENDING MARKETS ***
- PERFORMS BEST: In markets with clear, sustained trends
- AVOID USING: During sideways, choppy, or highly volatile markets
- IDEAL TIMEFRAMES: Daily charts for long-term trends, 1-hour for medium-term
- OPTIMAL MARKET CONDITION: Bull or bear markets with clear directional movement

The strategy will struggle in ranging or sideways markets where prices oscillate
without establishing a clear trend, resulting in multiple false signals and whipsaws.
It performs best when applied to instruments that exhibit persistent directional moves.

PARAMETER ADJUSTMENT:
--------------------
- For longer-term trends: Increase both MA periods (e.g., 50/200)
- For shorter-term trends: Decrease both MA periods (e.g., 10/30)
- For fewer signals: Increase the confirmation bars (2+)
- For faster responses: Use EMA instead of SMA

OPTIMIZED FOR:
-------------
- Timeframe: Daily charts for long-term trends, 1-hour for medium-term
- Year: 2024
- Market: Stocks with clear trending behavior
- Best Performance: During strong bull or bear markets

USAGE:
------
python strategies/moving_average_crossover.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

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

MOVING AVERAGE PARAMETERS:
-------------------------
--short-period, -sp  : Period for the short-term moving average (default: 50)
                      Shorter values respond faster to price changes but generate more signals.

--long-period, -lp   : Period for the long-term moving average (default: 200)
                      Longer values provide more reliable trend identification but are slower.

--ma-type, -mt       : Moving average type (default: SMA, options: SMA, EMA, WMA, SMMA)
                      EMA responds faster to recent price changes but can be noisier.

--confirmation, -cf  : Number of bars to confirm a crossover (default: 1)
                      Higher values reduce false signals but delay entries/exits.

RISK MANAGEMENT:
---------------
--stop-loss, -sl     : Stop loss percentage (default: 2.0)
                      The maximum loss allowed on a trade (% of entry price).

--trailing-stop, -ts : Enable trailing stop loss (default: False)
                      Locks in profits as the price moves favorably.

--trail-percent, -tp : Trailing stop percentage (default: 2.0)
                      Distance of trailing stop from highest price (%).

POSITION SIZING:
---------------
--risk-percent, -rp  : Percentage of equity to risk per trade (default: 1.0)
                      Controls how much of your account to risk on each position.

--max-position, -mp  : Maximum position size as percentage of equity (default: 20.0)
                      Limits the maximum exposure to any single trade.

TRADE THROTTLING:
---------------
--trade-throttle-days, -ttd : Minimum days between trades (default: 5, set to 0 for no throttling)
                             Reduces overtrading during highly volatile periods.

OTHER:
-----
--plot, -pl          : Generate and show a plot of the trading activity

EXAMPLE COMMANDS:
---------------
1. Standard configuration - classic 50/200 golden cross:
   python strategies/moving_average_crossover.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --short-period 50 --long-period 200 --ma-type SMA

2. Short-term trading - faster signals with EMA:
   python strategies/moving_average_crossover.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --short-period 20 --long-period 50 --ma-type EMA

3. Conservative approach - confirmation bars to reduce false signals:
   python strategies/moving_average_crossover.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --short-period 50 --long-period 200 --confirmation 3

4. Aggressive trading with tighter stops:
   python strategies/moving_average_crossover.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --short-period 10 --long-period 30 --stop-loss 1.5

5. Trailing stop approach - capture more of trending moves:
   python strategies/moving_average_crossover.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --trailing-stop --trail-percent 3.0

6. High risk-reward setup with weighted moving averages:
   python strategies/moving_average_crossover.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --short-period 15 --long-period 60 --ma-type WMA --risk-percent 2.0 --max-position 30

EXAMPLE:
--------
Basic usage:
python strategies/moving_average_crossover.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31

With confirmation parameter (wait for 2 bars of consistent signal):
python strategies/moving_average_crossover.py --data AAPL --confirmation 2 --trailing-stop

With faster moving averages (better for 1-hour timeframe):
python strategies/moving_average_crossover.py --data AAPL --short-period 20 --long-period 50 --ma-type EMA

With plotting:
python strategies/moving_average_crossover.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --short-period 50 --long-period 200 --plot
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

# Import utility functions
from strategies.utils import (
    TradeThrottling,
    add_standard_analyzers,
    get_db_data,
    print_performance_metrics,
)


class StockPriceData(bt.feeds.PandasData):
    """Stock Price Data Feed"""

    params = (
        ("datetime", None),
        ("open", "Open"),
        ("high", "High"),
        ("low", "Low"),
        ("close", "Close"),
        ("volume", "Volume"),
        ("openinterest", None),
    )


class MovingAverageCrossStrategy(bt.Strategy, TradeThrottling):
    """Moving Average Crossover Strategy

    This strategy generates buy and sell signals based on the crossover
    of a short-term moving average and a long-term moving average.

    A buy signal is generated when the short-term MA crosses above the long-term MA.
    A sell signal is generated when the short-term MA crosses below the long-term MA.

    ** IMPORTANT: This strategy is specifically designed for trending markets **
    It performs poorly in sideways or choppy markets where prices oscillate without
    establishing a clear trend.

    Strategy Logic:
    - Buy when the short-term MA crosses above the long-term MA
    - Sell when the short-term MA crosses below the long-term MA
    - Optional confirmation period to reduce false signals
    - Uses risk-based position sizing
    - Implements stop-loss and optional trailing stop

    Best Market Conditions:
    - Strong trending markets (either bullish or bearish)
    - Stocks with clear directional momentum
    - Lower volatility periods with sustained price direction
    - Avoid during range-bound, choppy, or highly volatile markets


    """

    params = (
        # Moving average parameters
        ("short_period", 50),  # Short MA period
        ("long_period", 200),  # Long MA period
        ("ma_type", "SMA"),  # Moving average type: SMA, EMA, WMA, SMMA
        ("confirmation", 1),  # Number of bars to confirm a crossover
        # Risk management parameters
        ("stop_loss", 2.0),  # Stop loss percentage
        ("trailing_stop", False),  # Use trailing stop loss
        ("trail_percent", 2.0),  # Trailing stop percentage
        # Position sizing parameters
        ("risk_percent", 1.0),  # Percentage of equity to risk per trade
        ("max_position", 20.0),  # Maximum position size as percentage
        # Trade throttling
        # Minimum days between trades (0 = no throttling)
        ("trade_throttle_days", 5),
        # Other parameters
        ("printlog", False),  # Print log to console
    )

    def log(self, txt, dt=None, doprint=False):
        """Log messages

        :param txt:
        :param dt:  (Default value = None)
        :param doprint:  (Default value = False)

        """
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()}: {txt}")

    def __init__(self):
        """ """
        # Keep a reference to the "close" line
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # Order and position tracking
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.stop_price = None
        self.trail_price = None
        self.highest_price = None

        # Confirmation tracking
        self.crossover_count = 0
        self.cross_direction = None  # 'up' or 'down'

        # For trade throttling
        self.last_trade_date = None

        # Create moving average indicators
        # First determine which MA type to use
        if self.p.ma_type == "SMA":
            ma_class = bt.indicators.SimpleMovingAverage
        elif self.p.ma_type == "EMA":
            ma_class = bt.indicators.ExponentialMovingAverage
        elif self.p.ma_type == "WMA":
            ma_class = bt.indicators.WeightedMovingAverage
        elif self.p.ma_type == "SMMA":
            ma_class = bt.indicators.SmoothedMovingAverage
        else:
            # Default to SMA
            ma_class = bt.indicators.SimpleMovingAverage

        # Create the moving averages
        self.ma_short = ma_class(self.datas[0], period=self.p.short_period)
        self.ma_long = ma_class(self.datas[0], period=self.p.long_period)

        # Create crossover indicator
        self.crossover = bt.indicators.CrossOver(self.ma_short, self.ma_long)

        # Add ATR for stop loss calculation
        self.atr = bt.indicators.ATR(self.datas[0], period=14)

    def notify_order(self, order):
        """Process order notifications

        :param order:

        """
        if order.status in [order.Submitted, order.Accepted]:
            # Order still in progress - do nothing
            return

        # Order completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED: Price: {order.executed.price:.2f}, "
                    f"Size: {order.executed.size}, "
                    f"Cost: {order.executed.value:.2f}, "
                    f"Comm: {order.executed.comm:.2f}"
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm

                # Set stop loss
                self.stop_price = self.buyprice * (1.0 - self.p.stop_loss / 100.0)
                self.log(
                    f"Stop loss set at: {self.stop_price:.2f} ({self.p.stop_loss}%)"
                )

                # Set trailing stop if enabled
                if self.p.trailing_stop:
                    self.trail_price = self.buyprice * (
                        1.0 - self.p.trail_percent / 100.0
                    )
                    self.highest_price = self.buyprice
                    self.log(
                        "Trailing stop set at:"
                        f" {self.trail_price:.2f} ({self.p.trail_percent}%)"
                    )

                # Update last trade date for throttling
                self.last_trade_date = self.datas[0].datetime.date(0)

            else:  # sell
                self.log(
                    f"SELL EXECUTED: Price: {order.executed.price:.2f}, "
                    f"Size: {order.executed.size}, "
                    f"Cost: {order.executed.value:.2f}, "
                    f"Comm: {order.executed.comm:.2f}"
                )
                # Reset stop and trail prices
                self.stop_price = None
                self.trail_price = None
                self.highest_price = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order {order.Status[order.status]}")

        # Reset the order
        self.order = None

    def notify_trade(self, trade):
        """Process trade notifications

        :param trade:

        """
        if not trade.isclosed:
            return

        self.log(f"OPERATION PROFIT, GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}")

    def calculate_position_size(self):
        """Calculate position size based on risk percentage"""
        current_price = self.dataclose[0]
        value = self.broker.getvalue()

        # Calculate stop loss price
        stop_price = current_price * (1.0 - self.p.stop_loss / 100.0)

        # Calculate risk amount based on portfolio value
        risk_amount = value * (self.p.risk_percent / 100)

        # Calculate risk per share
        risk_per_share = current_price - stop_price

        # Calculate position size based on risk
        if risk_per_share > 0:
            size = int(risk_amount / risk_per_share)

            # Ensure we don't exceed maximum percentage of available cash
            cash = self.broker.getcash()
            max_size = int((cash * self.p.max_position / 100) / current_price)
            size = min(size, max_size)

            return size

        return 0

    def next(self):
        """Main strategy logic executed for each bar"""
        # Skip if order is pending
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # BUY LOGIC

            # Check if we're allowed to trade based on the throttling rules
            if not self.can_trade_now():
                return

            # Check for a buy signal (short MA crossing above long MA)
            if self.crossover > 0:
                # Track the crossover for confirmation if needed
                if self.cross_direction != "up":
                    self.cross_direction = "up"
                    self.crossover_count = 1
                else:
                    self.crossover_count += 1

                # Check if we have enough confirmation bars
                if self.crossover_count >= self.p.confirmation:
                    # Calculate position size based on risk
                    size = self.calculate_position_size()

                    if size > 0:
                        self.log(f"BUY CREATE: {self.dataclose[0]:.2f}, Size: {size}")
                        self.order = self.buy(size=size)

                        # Store the highest price seen for trailing stop
                        self.highest_price = self.dataclose[0]

                        # Update the last trade date for throttling
                        self.last_trade_date = self.datas[0].datetime.date(0)
            else:
                # Reset counter if crossover direction changes
                if self.crossover < 0 and self.cross_direction != "down":
                    self.cross_direction = "down"
                    self.crossover_count = 1
                elif self.crossover < 0:
                    self.crossover_count += 1
                else:
                    self.crossover_count = 0
                    self.cross_direction = None

        else:
            # SELL LOGIC - We are in the market, look for a sell signal

            # Check for stop loss
            if self.datalow[0] <= self.stop_price:
                self.log(f"SELL CREATE (Stop Loss): {self.datalow[0]:.2f}")
                self.order = self.sell()
                return

            # Update trailing stop if enabled
            if self.p.trailing_stop and self.datahigh[0] > self.highest_price:
                self.highest_price = self.datahigh[0]
                # Calculate new trail stop price
                new_trail_price = self.highest_price * (
                    1.0 - self.p.trail_percent / 100.0
                )
                # Only update if the new trail price is higher than the current
                # one
                if new_trail_price > self.trail_price:
                    self.trail_price = new_trail_price
                    self.log(f"Trailing stop updated: {self.trail_price:.2f}")

            # Check if trailing stop is hit
            if self.p.trailing_stop and self.datalow[0] <= self.trail_price:
                self.log(f"SELL CREATE (Trailing Stop): {self.datalow[0]:.2f}")
                self.order = self.sell()
                return

            # Check for a sell signal (short MA crossing below long MA)
            if self.crossover < 0:
                # Track the crossover for confirmation if needed
                if self.cross_direction != "down":
                    self.cross_direction = "down"
                    self.crossover_count = 1
                else:
                    self.crossover_count += 1

                # Check if we have enough confirmation bars
                if self.crossover_count >= self.p.confirmation:
                    self.log(f"SELL CREATE: {self.dataclose[0]:.2f}")
                    self.order = self.sell()
            else:
                # Reset counter if crossover direction changes
                if self.crossover > 0 and self.cross_direction != "up":
                    self.cross_direction = "up"
                    self.crossover_count = 1
                elif self.crossover > 0:
                    self.crossover_count += 1
                else:
                    self.crossover_count = 0
                    self.cross_direction = None

    def stop(self):
        """Called when backtest is complete"""
        self.log("Moving Average Crossover Strategy completed", doprint=True)
        self.log(
            f"Final Portfolio Value: {self.broker.getvalue():.2f}",
            doprint=True,
        )

        # Add a note about market conditions
        self.log(
            "NOTE: This strategy is specifically designed for trending markets",
            doprint=True,
        )
        self.log(
            "      It performs poorly in sideways or choppy markets",
            doprint=True,
        )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Moving Average Crossover Strategy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Required arguments
    parser.add_argument(
        "--data", "-d", required=True, help="Stock symbol to retrieve data for"
    )

    # Date range arguments
    parser.add_argument(
        "--fromdate",
        "-f",
        type=str,
        default="2024-01-01",
        help="Start date for the backtest in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--todate",
        "-t",
        type=str,
        default="2024-12-31",
        help="End date for the backtest in YYYY-MM-DD format",
    )

    # Database arguments
    parser.add_argument("--dbuser", "-u", default="jason", help="PostgreSQL username")
    parser.add_argument("--dbpass", "-pw", default="fsck", help="PostgreSQL password")
    parser.add_argument(
        "--dbname", "-n", default="market_data", help="PostgreSQL database name"
    )

    # Strategy arguments
    parser.add_argument(
        "--cash",
        "-c",
        type=float,
        default=100000.0,
        help="Initial cash for the backtest",
    )

    # Moving average parameters
    parser.add_argument(
        "--short-period",
        "-sp",
        type=int,
        default=50,
        help="Period for short moving average",
    )
    parser.add_argument(
        "--long-period",
        "-lp",
        type=int,
        default=200,
        help="Period for long moving average",
    )
    parser.add_argument(
        "--ma-type",
        "-mt",
        type=str,
        default="SMA",
        choices=["SMA", "EMA", "WMA", "SMMA"],
        help="Moving average type",
    )
    parser.add_argument(
        "--confirmation",
        "-cf",
        type=int,
        default=1,
        help="Number of bars to confirm a crossover",
    )

    # Risk management parameters
    parser.add_argument(
        "--stop-loss",
        "-sl",
        type=float,
        default=2.0,
        help="Stop loss percentage",
    )
    parser.add_argument(
        "--trailing-stop",
        "-ts",
        action="store_true",
        help="Enable trailing stop loss",
    )
    parser.add_argument(
        "--trail-percent",
        "-tp",
        type=float,
        default=2.0,
        help="Trailing stop percentage",
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
        default=5,
        help="Minimum days between trades (0 = no throttling)",
    )

    # Other parameters
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

    # Get data from database
    df = get_db_data(args.data, args.dbuser, args.dbpass, args.dbname, fromdate, todate)

    # Create a Data Feed
    data = StockPriceData(dataname=df)

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add the data feed to cerebro
    cerebro.adddata(data)

    # Add strategy to cerebro
    cerebro.addstrategy(
        MovingAverageCrossStrategy,
        # Moving average parameters
        short_period=args.short_period,
        long_period=args.long_period,
        ma_type=args.ma_type,
        confirmation=args.confirmation,
        # Risk management parameters
        stop_loss=args.stop_loss,
        trailing_stop=args.trailing_stop,
        trail_percent=args.trail_percent,
        # Risk management parameters
        risk_percent=args.risk_percent,
        max_position=args.max_position,
        # Trade throttling
        trade_throttle_days=args.trade_throttle_days,
    )

    # Set initial cash
    cerebro.broker.setcash(args.cash)

    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)

    # Add the standard analyzers
    add_standard_analyzers(cerebro)

    # Print out the starting conditions
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Run the strategy
    results = cerebro.run()

    # Print final portfolio value
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: ${final_value:.2f}")
    print(f"Profit/Loss: ${final_value - args.cash:.2f}")

    # Print standard performance metrics
    print_performance_metrics(cerebro, results)

    # Extract and display detailed performance metrics
    print("\n==== DETAILED PERFORMANCE METRICS ====")

    # Get the first strategy instance
    strat = results[0]

    # Return
    ret_analyzer = strat.analyzers.returns
    total_return = ret_analyzer.get_analysis()["rtot"] * 100
    print(f"Return: {total_return:.2f}%")

    # Sharpe Ratio
    sharpe = strat.analyzers.sharpe_ratio.get_analysis()["sharperatio"]
    if sharpe is None:
        sharpe = 0.0
    print(f"Sharpe Ratio: {sharpe:.4f}")

    # Max Drawdown
    dd = strat.analyzers.drawdown.get_analysis()
    max_dd = dd.get("max", {}).get("drawdown", 0.0)
    print(f"Max Drawdown: {max_dd:.2f}%")

    # Trade statistics
    trade_analysis = strat.analyzers.trade_analyzer.get_analysis()

    # Total Trades
    total_trades = trade_analysis.get("total", {}).get("total", 0)
    print(f"Total Trades: {total_trades}")

    # Won Trades
    won_trades = trade_analysis.get("won", {}).get("total", 0)
    print(f"Won Trades: {won_trades}")

    # Lost Trades
    lost_trades = trade_analysis.get("lost", {}).get("total", 0)
    print(f"Lost Trades: {lost_trades}")

    # Win Rate
    if total_trades > 0:
        win_rate = (won_trades / total_trades) * 100
    else:
        win_rate = 0.0
    print(f"Win Rate: {win_rate:.2f}%")

    # Average Win
    avg_win = trade_analysis.get("won", {}).get("pnl", {}).get("average", 0.0)
    print(f"Average Win: ${avg_win:.2f}")

    # Average Loss
    avg_loss = trade_analysis.get("lost", {}).get("pnl", {}).get("average", 0.0)
    print(f"Average Loss: ${avg_loss:.2f}")

    # Profit Factor
    gross_profit = trade_analysis.get("won", {}).get("pnl", {}).get("total", 0.0)
    gross_loss = abs(trade_analysis.get("lost", {}).get("pnl", {}).get("total", 0.0))

    if gross_loss != 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = float("inf") if gross_profit > 0 else 0.0

    print(f"Profit Factor: {profit_factor:.2f}")

    # Plot the result if requested
    if args.plot:
        cerebro.plot(style="candlestick", barup="green", bardown="red")


if __name__ == "__main__":
    main()
