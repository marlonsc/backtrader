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
"""RISK AVERSE STRATEGY WITH POSTGRESQL DATABASE - (risk_adverse)
===============================================================================
This strategy is designed to buy stocks that exhibit specific characteristics of stability
and controlled momentum. It identifies securities with:
- Low volatility (stable price movement)
- Recent new highs (positive momentum)
- High trading volume (market interest)
- Small difference between high and low prices (price consolidation)
These combined factors aim to find stocks that are stable but still have upward
momentum, reducing the risk associated with high volatility while still capturing
growth opportunities.
STRATEGY LOGIC:
--------------
- GO LONG when ALL of the following conditions are met:
1. Volatility is below a specified threshold
2. Price has recently made a new high
3. Volume is above a minimum threshold
4. The high-low price difference is below a specified threshold
- EXIT LONG when TWO OR MORE of the above conditions are no longer valid
This ensures we exit positions when the stock no longer exhibits the
favorable risk-reward characteristics we seek.
MARKET CONDITIONS:
----------------
- Best used in moderately bullish markets
- Works well for stocks in consolidation phases that are preparing to move higher
- Avoids highly volatile stocks that may experience sharp price drops
- Most effective in sectors with steady growth rather than cyclical or highly speculative areas
VOLATILITY ASSESSMENT:
-------------------
The strategy calculates average volatility over a specified period to assess price stability.
Low volatility suggests:
- More predictable price action
- Lower risk of sharp adverse price movements
- Better potential risk-reward ratio
NEW HIGH DETECTION:
----------------
The strategy monitors when a security makes a new high within a lookback period:
- Indicates positive momentum
- Suggests underlying strength
- Identifies potential breakout candidates
VOLUME ANALYSIS:
-------------
High trading volume is required as it:
- Indicates market interest in the security
- Provides liquidity for entries and exits
- Validates price movement as significant
HIGH-LOW DIFFERENTIAL:
-------------------
Small differences between high and low prices indicate:
- Controlled price movement (not erratic)
- Potential consolidation before further movement
- Reduced intraday volatility
RISK MANAGEMENT:
--------------
The strategy employs a unique exit criterion that monitors multiple factors:
- Exits when 2+ conditions are no longer favorable
- Responsive to changing market conditions
- Adapts to deteriorating security-specific metrics
USAGE:
------
python strategies/risk_adverse.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]
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
VOLATILITY PARAMETERS:
-------------------
--volatility-period, -vp   : Period for volatility calculation (default: 20)
This determines how many bars are used to calculate average volatility.
Longer periods provide more stable measurements but may be less responsive
to recent market changes.
--volatility-threshold, -vt : Maximum allowed volatility (default: 8.0)
Lower values create stricter entry criteria requiring more stable stocks.
Higher values are more permissive, allowing more volatile stocks.
The value represents percentage volatility (e.g., 8.0 = 8% average volatility).
HIGH-LOW PARAMETERS:
-----------------
--high-low-period, -hlp    : Period for high-low difference calculation (default: 60)
This determines how many bars are used to assess the high-low price range.
Longer periods capture longer-term price behavior.
--high-low-threshold, -hlt : Maximum allowed high-low difference (default: 0.3)
Expressed as a ratio of the difference to price.
Lower values require more consolidated price action.
Higher values allow wider price ranges.
VOLUME PARAMETERS:
---------------
--vol-period, -volp        : Period for volume moving average (default: 5)
Determines how many bars are used to calculate average volume.
Shorter periods make the strategy more responsive to recent volume changes.
--vol-threshold, -volt     : Minimum required volume (default: 100000)
Sets the minimum trading volume required for entry.
Should be adjusted based on the typical volume of the target stock.
Higher values ensure greater liquidity.
EXIT PARAMETERS:
---------------
--exit-count, -ec          : Number of failed conditions required for exit (default: 2)
Higher values make exits more conservative (require more conditions to fail).
Lower values make exits more aggressive (fewer conditions need to fail).
POSITION SIZING:
---------------
--position-percent, -pp    : Percentage of equity to use per trade (default: 20.0)
Controls how much of your account to risk on each position.
Higher values increase potential returns but also increase risk.
--max-position, -mp        : Maximum position size as percentage of equity (default: 95.0)
Prevents over-leveraging by limiting the maximum position size.
OTHER:
-----
--plot, -pl               : Generate and show a plot of the trading activity
Shows price data, indicators, and entry/exit points.
EXAMPLE COMMANDS:
---------------
Basic usage:
python strategies/risk_adverse.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31
Conservative settings:
python strategies/risk_adverse.py --data MSFT --volatility-threshold 5.0 --high-low-threshold 0.2 --vol-threshold 150000
More permissive settings:
python strategies/risk_adverse.py --data TSLA --volatility-threshold 12.0 --high-low-threshold 0.5 --exit-count 3
Adjusting lookback periods:
python strategies/risk_adverse.py --data GOOGL --volatility-period 15 --high-low-period 40 --vol-period 3"""

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
        ("openinterest", None),  # Column for open interest (not available)
    )


class AverageVolatility(bt.Indicator):
    """Average Volatility Indicator
Calculates the average volatility over a specified period as percentage change
from close to close.
Lines:
- avg_volatility: Average volatility as a percentage"""

    lines = ("avg_volatility",)
    params = dict(period=20)

    def __init__(self):
""""""
    """Recent High Indicator
Detects if the current price is a new high within a specified lookback period.
Lines:
- new_high: 1 if current price is a new high, 0 otherwise"""

    lines = ("new_high",)
    params = dict(lookback=20)

    def __init__(self):
""""""
    """Difference High Low Indicator
Calculates the ratio of the difference between the highest high and lowest low
to the average price over a specified period.
Lines:
- diff: The ratio of high-low difference to average price"""

    lines = ("diff",)
    params = dict(period=60)

    def __init__(self):
""""""
    """Risk Averse Strategy
This strategy seeks to buy stocks with low volatility, recent new highs, high volume,
and small differences between high and low prices. It exits positions when multiple
conditions deteriorate.
The goal is to find stable stocks with controlled upward momentum while minimizing
exposure to erratic price movements.
Strategy Logic:
- Buy when volatility is low, price is near highs, and volume is strong
- Exit when conditions deteriorate (high volatility, price weakness)
- Uses risk-based position sizing for proper money management
- Implements cool down period to avoid overtrading
Best Market Conditions:
- Stable bull markets with low volatility
- Sectors with steady growth rather than erratic momentum
- Quality stocks with consistent institutional buying
- Avoid using in highly volatile or bear markets"""

    params = (
        # Volatility parameters
        ("volatility_period", 20),  # Period for volatility calculation
        ("volatility_threshold", 8.0),  # Maximum allowed volatility percentage
        # High-Low parameters
        ("high_low_period", 60),  # Period for high-low analysis
        (
            "high_low_threshold",
            0.3,
        ),  # Maximum allowed high-low difference ratio
        # Volume parameters
        ("vol_period", 5),  # Period for volume moving average
        ("vol_threshold", 100000),  # Minimum required volume
        # Exit parameters
        ("exit_count", 2),  # Number of failed conditions required for exit
        # Position sizing
        ("position_size", 0.2),  # Percentage of portfolio to use per position
        ("max_position_pct", 95.0),  # Maximum position size as percentage
        # Risk management
        ("risk_percent", 1.0),  # Percentage of equity to risk per trade
        ("stop_pct", 2.0),  # Stop loss percentage below entry
        ("trail_pct", 2.0),  # Trailing stop percentage
        ("use_stop_loss", True),  # Use a stop loss
        ("use_trailing_stop", True),  # Use a trailing stop
        # Trade throttling
        ("trade_throttle_days", 5),  # Minimum days between trades
        # Logging parameters
        ("log_level", "info"),  # Logging level: 'debug', 'info'
    )

    def log(self, txt, dt=None, level="info"):
"""Logging function for the strategy

Args::
    txt: 
    dt: (Default value = None)
    level: (Default value = "info")"""
    level: (Default value = "info")"""
        if level == "debug" and self.params.log_level != "debug":
            return

        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}: {txt}")

    def __init__(self):
""""""
"""Calculate how many shares to buy based on position sizing rules

Args::
    price:"""
    price:"""
        available_cash = self.broker.get_cash()
        value = self.broker.getvalue()
        current_price = price

        # Calculate position size based on risk percentage if stop loss is
        # enabled
        if self.params.use_stop_loss:
            # Calculate the risk amount in dollars
            risk_amount = value * (self.params.risk_percent / 100.0)

            # Calculate the stop loss price
            stop_price = current_price * (1.0 - self.params.stop_pct / 100.0)

            # Calculate the risk per share
            risk_per_share = current_price - stop_price

            if risk_per_share > 0:
                # Calculate position size based on risk
                risk_based_size = int(risk_amount / risk_per_share)

                # Calculate size based on fixed percentage of equity
                equity_based_size = int(
                    (value * self.params.position_size) / current_price
                )

                # Use the smaller of the two sizes
                size = min(risk_based_size, equity_based_size)
            else:
                # If risk per share is zero or negative, use equity-based
                # sizing
                size = int((value * self.params.position_size) / current_price)
        else:
            # Fixed percentage of available equity without risk-based
            # calculation
            cash_to_use = value * self.params.position_size

            # Make sure we don't exceed maximum available cash
            max_cash = available_cash * (self.params.max_position_pct / 100.0)
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

        # Extra information about strategy settings
        self.log(
            f"Strategy Settings: Volatility({self.params.volatility_period},"
            f" {self.params.volatility_threshold}%), "
            + f"High-Low({self.params.high_low_period},"
            f" {self.params.high_low_threshold}), "
            + f"Volume({self.params.vol_period}, {self.params.vol_threshold})"
        )

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
        description="Risk Averse Strategy",
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

    # Volatility parameters
    parser.add_argument(
        "--volatility-period",
        "-vp",
        default=20,
        type=int,
        help="Period for volatility calculation",
    )

    parser.add_argument(
        "--volatility-threshold",
        "-vt",
        default=8.0,
        type=float,
        help="Maximum allowed volatility percentage",
    )

    # High-Low parameters
    parser.add_argument(
        "--high-low-period",
        "-hlp",
        default=60,
        type=int,
        help="Period for high-low difference calculation",
    )

    parser.add_argument(
        "--high-low-threshold",
        "-hlt",
        default=0.3,
        type=float,
        help="Maximum allowed high-low difference ratio",
    )

    # Volume parameters
    parser.add_argument(
        "--vol-period",
        "-volp",
        default=5,
        type=int,
        help="Period for volume moving average",
    )

    parser.add_argument(
        "--vol-threshold",
        "-volt",
        default=100000,
        type=int,
        help="Minimum required volume",
    )

    # Exit parameters
    parser.add_argument(
        "--exit-count",
        "-ec",
        default=2,
        type=int,
        help="Number of failed conditions required for exit",
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
        "--max-position",
        "-mp",
        default=95.0,
        type=float,
        help="Maximum position size as percentage of equity",
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

    # Add the Risk Averse strategy
    cerebro.addstrategy(
        RiskAverseStrategy,
        # Volatility parameters
        volatility_period=args.volatility_period,
        volatility_threshold=args.volatility_threshold,
        # High-Low parameters
        high_low_period=args.high_low_period,
        high_low_threshold=args.high_low_threshold,
        # Volume parameters
        vol_period=args.vol_period,
        vol_threshold=args.vol_threshold,
        # Exit parameters
        exit_count=args.exit_count,
        # Position sizing parameters
        position_size=args.position_percent / 100,  # Convert percentage to decimal
        max_position_pct=args.max_position,
    )

    # Set our desired cash start
    cerebro.broker.setcash(args.cash)

    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Set slippage to 0 (as required)
    cerebro.broker.set_slippage_perc(0.0)

    # Add analyzers using standard function
    add_standard_analyzers(cerebro)

    # Print out the starting conditions
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Print strategy configuration
    print("\nStrategy Configuration:")
    print(f"- Data Source: PostgreSQL database ({args.dbname})")
    print(f"- Symbol: {args.data}")
    print(f"- Date Range: {args.fromdate} to {args.todate}")
    print(
        f"- Volatility: Max {args.volatility_threshold}% over"
        f" {args.volatility_period} periods"
    )
    print(
        f"- High-Low Diff: Max {args.high_low_threshold} over"
        f" {args.high_low_period} periods"
    )
    print(f"- Volume: Min {args.vol_threshold} with {args.vol_period}-period average")
    print(f"- Exit: When {args.exit_count} or more conditions fail")
    print(
        f"- Position Sizing: Using {args.position_percent}% of equity per trade (max"
        f" {args.max_position}%)"
    )

    print("\n--- Starting Backtest ---\n")

    # Run the strategy
    results = cerebro.run()

    # Print out final results
    print("\n--- Backtest Results ---\n")
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():.2f}")

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
