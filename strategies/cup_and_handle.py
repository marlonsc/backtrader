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
"""CUP AND HANDLE TRADING STRATEGY WITH POSTGRESQL DATABASE - (cup-and-handle)
==================================================================
This strategy implements the Cup and Handle pattern, a bullish chart formation
that signals a potential breakout. The pattern consists of a U-shaped "cup"
followed by a smaller downward drift known as the "handle". A breakout above
the handle's resistance level is considered a buy signal.
STRATEGY LOGIC:
--------------
- Identify the formation of a U-shaped consolidation (the "cup")
- Detect a small pullback (the "handle") following the cup formation
- Generate a buy signal when the price breaks out above the handle resistance level
- Set a target price by measuring the depth of the cup and projecting it upwards
- Incorporate volume confirmation to validate the pattern
MARKET CONDITIONS:
----------------
*** THIS STRATEGY IS SPECIFICALLY DESIGNED FOR STOCKS FORMING BASE PATTERNS AFTER PULLBACKS ***
- PERFORMS BEST: After market corrections or in stocks consolidating after a prior uptrend
- AVOID USING: During bear markets or when stocks are making new lows
- IDEAL TIMEFRAMES: Daily and weekly charts
- OPTIMAL MARKET CONDITION: Bullish market conditions with proper sector rotation
This strategy is based on William O'Neil's CANSLIM method and works best when
the overall market is in an uptrend and the stock has strong fundamentals.
The cup should form a proper U-shape (not V-shape) and the handle should have
a gentle downward drift with declining volume.
USAGE:
------
python strategies/cup_and_handle.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]
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
CUP AND HANDLE PARAMETERS:
------------------------
--cup-length, -cl : Minimum length of the cup in bars (default: 30)
--handle-length, -hl : Minimum length of the handle in bars (default: 10)
--cup-depth, -cd : Minimum depth of the cup as a percentage (default: 15.0)
--handle-depth, -hd : Maximum depth of the handle as a percentage (default: 15.0)
--breakout-threshold, -bt : Percentage above handle high for breakout (default: 3.0)
--volume-mult, -vm : Volume multiplier for breakout confirmation (default: 1.2)
--target-mult, -tm : Multiplier for setting the target price (default: 1.0)
EXIT PARAMETERS:
---------------
--use-stop, -us : Whether to use a stop loss (default: False)
--stop-pct, -sp : Stop loss percentage from entry (default: 10.0)
--use-rsi-exit, -ure : Use RSI-based exit (default: True)
--rsi-overbought, -ro : RSI level considered overbought for exit (default: 70)
POSITION SIZING:
---------------
--risk-percent, -rp  : Percentage of equity to risk per trade (default: 1.0)
--max-position, -mp  : Maximum position size as percentage of equity (default: 20.0)
TRADE THROTTLING:
---------------
--trade-throttle-days, -ttd : Minimum days between trades (default: 5)
OTHER:
-----
--plot, -p      : Generate and show a plot of the trading activity
EXAMPLE:
--------
python strategies/cup_and_handle.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --cup-length 20 --handle-length 5 --plot"""

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

# Import utility functions
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


class StockPriceData(bt.feeds.PandasData):
    """Stock Price Data Feed"""

    lines = ("rsi",)  # Add RSI as a line

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


class CupAndHandleStrategy(bt.Strategy, TradeThrottling):
    """Cup and Handle Strategy with Volume Confirmation
This strategy identifies the classic Cup and Handle pattern and trades breakouts:
1. Identifies a U-shaped consolidation period (the "cup")
2. Detects a smaller pullback (the "handle") following the cup formation
3. Buys when price breaks out above the handle with volume confirmation
4. Sets a profit target based on the depth of the cup
Exit mechanisms include:
- Taking profit at the target price
- Stop loss to limit potential losses
- RSI-based exit when the stock becomes overbought
Pattern Validation:
- Cup must form a proper U-shape (not V-shape)
- Cup depth typically 15-30% (neither too shallow nor too deep)
- Handle should be less than 15% of cup depth
- Handle must form in the upper half of the cup
- Volume should decline during cup formation and handle
- Volume should surge during breakout
** IMPORTANT: This strategy is designed for stocks forming base patterns after pullbacks **
It performs best in bullish markets and should be avoided during bear markets."""

    params = (
        # Cup and Handle parameters
        ("cup_length", 30),  # Minimum length of the cup in bars
        ("handle_length", 10),  # Minimum length of the handle in bars
        ("cup_depth", 15.0),  # Minimum depth of the cup as a percentage
        ("handle_depth", 15.0),  # Maximum depth of the handle as a percentage
        (
            "breakout_threshold",
            3.0,
        ),  # Percentage above handle high for breakout
        ("volume_mult", 1.2),  # Volume multiplier for breakout confirmation
        ("target_mult", 1.0),  # Multiplier for setting the target price
        # Volume confirmation parameters
        (
            "volume_decline_pct",
            15.0,
        ),  # Required volume decline during cup formation (%)
        ("handle_vol_max", 85.0),  # Maximum handle volume as % of cup average
        # Minimum breakout volume as % of recent average
        ("breakout_vol_min", 150.0),
        ("volume_avg_period", 20),  # Period for volume moving average
        # Pattern validation parameters
        (
            "u_shape_ratio",
            0.5,
        ),  # Minimum ratio of middle/edges for U-shape (vs V-shape)
        # Handle must form in upper half of cup (%)
        ("handle_position_min", 50.0),
        # Exit parameters
        ("use_stop", True),  # Whether to use a stop loss
        ("stop_pct", 10.0),  # Stop loss percentage from entry
        ("use_rsi_exit", True),  # Use RSI-based exit
        ("rsi_overbought", 70),  # RSI level considered overbought for exit
        ("rsi_period", 14),  # Period for RSI calculation
        # Risk management
        ("risk_percent", 1.0),  # Percentage of equity to risk per trade
        ("max_position", 20.0),  # Maximum position size as percentage of equity
        # Trade throttling
        ("trade_throttle_days", 5),  # Minimum days between trades
        # Logging parameters
        ("log_level", "info"),  # Logging level (debug, info, warning, error)
    )

    def log(self, txt, dt=None, level="info"):
"""Logging function

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
        """Calculate position size based on risk percentage"""
        cash = self.broker.getcash()
        value = self.broker.getvalue()
        current_price = self.dataclose[0]

        # If using stop loss, calculate based on risk
        if self.p.use_stop:
            # Calculate size based on risk percentage
            risk_amount = value * (self.p.risk_percent / 100)
            stop_price = current_price * (1 - self.p.stop_pct / 100)
            risk_per_share = current_price - stop_price

            if risk_per_share > 0:
                size = int(risk_amount / risk_per_share)
            else:
                # Fallback calculation based on max position
                size = int((value * self.p.max_position / 100) / current_price)
        else:
            # If not using stop loss, use max position percentage
            size = int((value * self.p.max_position / 100) / current_price)

        # Make sure we don't exceed maximum position size or available cash
        # Use 95% of available cash at most
        max_size = int((cash * 0.95) / current_price)
        return min(size, max_size)

    def notify_order(self, order):
"""Args::
    order:"""
"""Args::
    trade:"""
        """Reset pattern detection variables"""
        self.cup_stage = True  # We start by looking for a cup
        self.handle_stage = False  # Then we look for a handle
        self.breakout_stage = False  # Then we look for a breakout

        self.cup_bars = 0  # Number of bars in the cup
        self.handle_bars = 0  # Number of bars in the handle

        self.cup_high = 0  # Highest price in the cup
        self.cup_low = float("inf")  # Lowest price in the cup
        self.handle_high = 0  # Highest price in the handle
        self.handle_low = float("inf")  # Lowest price in the handle

        self.cup_start_idx = 0  # Starting index of the cup
        self.cup_bottom_idx = 0  # Index of the cup bottom
        self.cup_end_idx = 0  # Ending index of the cup
        self.handle_start_idx = 0  # Starting index of the handle

        self.cup_volumes = []  # Volumes during cup formation
        self.handle_volumes = []  # Volumes during handle formation

        self.cup_left_price = None  # Price at the left side of the cup
        self.cup_bottom_price = None  # Price at the bottom of the cup
        self.cup_right_price = None  # Price at the right side of the cup
        self.handle_high_price = None  # Price at the top of the handle
        self.handle_low_price = None  # Price at the bottom of the handle

    def is_valid_cup_shape(self):
        """Validate if the cup has a proper U-shape rather than a V-shape"""
        if (
            not self.cup_bottom_idx
            or self.cup_bottom_idx <= self.cup_start_idx
            or self.cup_end_idx <= self.cup_bottom_idx
        ):
            return False

        # Get price at the middle of the cup (should be near the bottom for
        # U-shape)
        cup_middle_price = self.dataclose[-(len(self) - self.cup_bottom_idx)]

        # Get prices at quarter points of the cup
        quarter_idx = (
            self.cup_start_idx + (self.cup_bottom_idx - self.cup_start_idx) // 2
        )
        three_quarter_idx = (
            self.cup_bottom_idx + (self.cup_end_idx - self.cup_bottom_idx) // 2
        )

        quarter_price = self.dataclose[-(len(self) - quarter_idx)]
        three_quarter_price = self.dataclose[-(len(self) - three_quarter_idx)]

        # For a U-shape: middle should be significantly lower than quarter points
        # This ratio should be less than 1.0 for a U-shape, closer to 1.0 for a
        # V-shape
        left_ratio = (cup_middle_price - self.cup_low) / (quarter_price - self.cup_low)
        right_ratio = (cup_middle_price - self.cup_low) / (
            three_quarter_price - self.cup_low
        )

        # U-shape validation: both ratios should be less than the threshold
        u_shape_valid = (
            left_ratio < self.p.u_shape_ratio and right_ratio < self.p.u_shape_ratio
        )

        if u_shape_valid:
            self.log(
                f"Valid U-shape cup: left ratio={left_ratio:.2f}, right"
                f" ratio={right_ratio:.2f}",
                level="debug",
            )
        else:
            self.log(
                f"Invalid cup shape (V-shaped): left ratio={left_ratio:.2f}, right"
                f" ratio={right_ratio:.2f}",
                level="warning",
            )

        return u_shape_valid

    def is_valid_handle_position(self):
        """Check if the handle forms in the upper half of the cup"""
        if not self.cup_high or not self.cup_low:
            return False

        # Calculate cup range
        cup_range = self.cup_high - self.cup_low

        # Check if handle forms in the upper half of the cup range
        handle_position = ((self.handle_low - self.cup_low) / cup_range) * 100

        valid = handle_position >= self.p.handle_position_min

        if valid:
            self.log(
                f"Valid handle position: {handle_position:.1f}% up from cup bottom",
                level="debug",
            )
        else:
            self.log(
                f"Invalid handle position: {handle_position:.1f}% (minimum required:"
                f" {self.p.handle_position_min}%)",
                level="warning",
            )

        return valid

    def is_valid_volume_pattern(self):
        """Validate the volume pattern for the cup and handle formation"""
        if not self.cup_volumes or not self.handle_volumes:
            return False

        # Calculate average volume during the cup formation
        cup_avg_volume = sum(self.cup_volumes) / len(self.cup_volumes)

        # Check for volume decline during cup formation
        # Average of first 5 bars
        cup_start_vol = sum(self.cup_volumes[:5]) / 5
        cup_end_vol = sum(self.cup_volumes[-5:]) / 5  # Average of last 5 bars

        vol_decline = ((cup_start_vol - cup_end_vol) / cup_start_vol) * 100
        vol_decline_valid = vol_decline >= self.p.volume_decline_pct

        # Check handle volume (should be lower than cup average)
        handle_avg_volume = sum(self.handle_volumes) / len(self.handle_volumes)
        handle_vol_pct = (handle_avg_volume / cup_avg_volume) * 100
        handle_vol_valid = handle_vol_pct <= self.p.handle_vol_max

        # Current volume for potential breakout
        breakout_vol_pct = (self.datavolume[0] / self.volume_ma[0]) * 100
        breakout_vol_valid = breakout_vol_pct >= self.p.breakout_vol_min

        valid = vol_decline_valid and handle_vol_valid

        if valid:
            self.log(
                f"Valid volume pattern: cup decline={vol_decline:.1f}%, handle"
                f" vol={handle_vol_pct:.1f}% of cup",
                level="debug",
            )
        else:
            self.log(
                f"Invalid volume pattern: cup decline={vol_decline:.1f}%, handle"
                f" vol={handle_vol_pct:.1f}%",
                level="warning",
            )

        return valid, breakout_vol_valid

    def next(self):
""""""
        """Called when backtest is complete"""
        self.log("Cup and Handle Strategy completed")
        self.log(f"Final Portfolio Value: {self.broker.getvalue():.2f}")

        # Add a note about market conditions
        self.log(
            "NOTE: This strategy is specifically designed for stocks forming base"
            " patterns"
        )
        self.log("      after pullbacks in bullish market conditions")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=(
            "Cup and Handle Pattern Strategy with data from PostgreSQL database"
        ),
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

    # Cup and Handle parameters
    parser.add_argument(
        "--cup-length",
        "-cl",
        default=30,
        type=int,
        help="Minimum length of the cup in bars",
    )

    parser.add_argument(
        "--handle-length",
        "-hl",
        default=10,
        type=int,
        help="Minimum length of the handle in bars",
    )

    parser.add_argument(
        "--cup-depth",
        "-cd",
        default=15.0,
        type=float,
        help="Minimum depth of the cup as a percentage",
    )

    parser.add_argument(
        "--handle-depth",
        "-hd",
        default=15.0,
        type=float,
        help="Maximum depth of the handle as a percentage",
    )

    parser.add_argument(
        "--breakout-threshold",
        "-bt",
        default=3.0,
        type=float,
        help="Percentage above handle high for breakout",
    )

    parser.add_argument(
        "--volume-mult",
        "-vm",
        default=1.2,
        type=float,
        help="Volume multiplier for breakout confirmation",
    )

    parser.add_argument(
        "--target-mult",
        "-tm",
        default=1.0,
        type=float,
        help="Multiplier for setting the target price",
    )

    # Exit parameters
    parser.add_argument("--use-stop", "-us", action="store_true", help="Use stop loss")

    parser.add_argument(
        "--stop-pct",
        "-sp",
        default=10.0,
        type=float,
        help="Stop loss percentage from entry",
    )

    parser.add_argument(
        "--use-rsi-exit", "-ure", action="store_true", help="Use RSI-based exit"
    )

    parser.add_argument(
        "--rsi-overbought",
        "-ro",
        default=70,
        type=int,
        help="RSI level considered overbought for exit",
    )

    # Position sizing parameters
    parser.add_argument(
        "--risk-percent",
        "-rp",
        default=1.0,
        type=float,
        help="Percentage of equity to risk per trade",
    )

    parser.add_argument(
        "--max-position",
        "-mp",
        default=20.0,
        type=float,
        help="Maximum position size as percentage of equity",
    )

    # Trade throttling
    parser.add_argument(
        "--trade-throttle-days",
        "-ttd",
        default=5,
        type=int,
        help="Minimum days between trades",
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

    # Add strategy with parameters
    cerebro.addstrategy(
        CupAndHandleStrategy,
        # Cup and Handle parameters
        cup_length=args.cup_length,
        handle_length=args.handle_length,
        cup_depth=args.cup_depth,
        handle_depth=args.handle_depth,
        breakout_threshold=args.breakout_threshold,
        volume_mult=args.volume_mult,
        target_mult=args.target_mult,
        # Exit parameters
        use_stop=args.use_stop,
        stop_pct=args.stop_pct,
        use_rsi_exit=args.use_rsi_exit,
        rsi_overbought=args.rsi_overbought,
        # Position sizing parameters
        risk_percent=args.risk_percent,
        max_position=args.max_position,
        # Trade throttling
        trade_throttle_days=args.trade_throttle_days,
        # Logging
        log_level="info",
    )

    # Set our desired cash start
    cerebro.broker.setcash(args.cash)

    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)

    # Set slippage to 0
    cerebro.broker.set_slippage_perc(0.0)

    # Add standard analyzers
    add_standard_analyzers(cerebro)

    # Print out the starting conditions
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Print strategy configuration
    print("\nStrategy Configuration:")
    print(f"- Symbol: {args.data}")
    print(f"- Date Range: {args.fromdate} to {args.todate}")
    print("\nCup and Handle Parameters:")
    print(f"- Cup Length: {args.cup_length} bars")
    print(f"- Handle Length: {args.handle_length} bars")
    print(f"- Cup Depth: {args.cup_depth}% minimum")
    print(f"- Handle Depth: {args.handle_depth}% maximum")
    print(f"- Breakout Threshold: {args.breakout_threshold}% above handle high")
    print(f"- Volume Confirmation: {args.volume_mult}x average cup volume")
    print(f"- Target Multiplier: {args.target_mult}x cup depth")

    print("\nExit Parameters:")
    if args.use_stop:
        print(f"- Stop Loss: {args.stop_pct}% from entry")
    else:
        print("- Stop Loss: Disabled")

    if args.use_rsi_exit:
        print(f"- RSI Exit: Enabled (RSI > {args.rsi_overbought})")
    else:
        print("- RSI Exit: Disabled")

    print(
        f"\nPosition Sizing: {args.risk_percent}% risk per trade (max"
        f" {args.max_position}%)"
    )

    if args.trade_throttle_days > 0:
        print(f"Trade Throttling: {args.trade_throttle_days} days between trades")

    print("\n--- Starting Backtest ---\n")
    print(
        "NOTE: This strategy is specifically designed for stocks forming base patterns"
    )
    print("      after pullbacks in bullish market conditions\n")

    # Run the strategy
    results = cerebro.run()

    # Print final portfolio value
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: ${final_value:.2f}")

    # Print standard performance metrics using standardized function
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
