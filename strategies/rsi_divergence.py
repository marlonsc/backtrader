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
"""RSI DIVERGENCE TRADING STRATEGY - (rsi-divergence)
==================================================
This strategy identifies and trades on RSI divergences:
- Bullish divergence: Price makes a lower low while RSI makes a higher low (oversold)
- Bearish divergence: Price makes a higher high while RSI makes a lower high (overbought)
STRATEGY LOGIC:
--------------
- Identify RSI divergences by comparing price lows/highs with RSI lows/highs
- Enter long on bullish divergence when price is in an uptrend or crosses above SMA
- Enter short on bearish divergence when price is in a downtrend or crosses below SMA
- Apply position sizing based on risk management (ATR-based stops)
- Use multiple exit mechanisms including trailing stops and RSI thresholds
MARKET CONDITIONS:
----------------
*** THIS STRATEGY PERFORMS BEST IN TRENDING MARKETS WITH PULLBACKS ***
It looks for price corrections against the main trend that aren't confirmed
by momentum (RSI), signaling potential trend resumption.
Here are a few initial suggestions for optimizing the RSI divergence strategy for TSLA:
1. Experiment with different RSI periods between 8-25. The default of 14 may not be optimal for TSLA. Shorter periods will be more sensitive and generate more signals.
2. Try a few different divergence lookback periods from 15-30 bars. The sweet spot is likely in the 20-25 range for catching meaningful divergences on TSLA.
3. For trend confirmation, test a short term 10 or 20-period SMA in addition to the default 50. TSLA can have some sharp momentum and a faster SMA may help ride those moves.
4. Consider widening the RSI overbought threshold to 75-80 and oversold to 20-25 to focus on only the most extreme divergences. TSLA has a lot of volatility.
5. Optimize the exit RSI thresholds separately for long and short trades. For TSLA longs, try exiting on RSI crossing back below 50-60. For shorts, exit when RSI crosses back above 40-50.
6. Backtest different risk per trade levels from 0.5% to 2%. Given TSLA's volatility, taking smaller position sizes with wider stops may improve consistency.
7. Try a trailing stop that follows the low of the past 5-10 bars in addition to the ATR stop. This can help ride TSLA's momentum.
8. If trading frequently, tighten up the throttling to 2-3 days between entries to reduce overtrading and whipsaw losses.
The key is finding the parameter combination that best captures TSLA's specific price action and volatility patterns.
EXAMPLE COMMANDS:
---------------
1. Standard configuration - default RSI divergence detection:
python strategies/rsi_divergence.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31
2. More sensitive RSI settings - faster divergence signals:
python strategies/rsi_divergence.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --rsi-period 10 --divergence-lookback 15
3. Extreme overbought/oversold thresholds - fewer but stronger signals:
python strategies/rsi_divergence.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --rsi-oversold 25 --rsi-overbought 75 --exit-rsi-thresh 40 --exit-rsi-thresh-short 60
4. Trend-filtered approach - stronger trend confirmation:
python strategies/rsi_divergence.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --trend-sma 100
5. Aggressive risk/reward profile - larger position sizing with wider stops:
python strategies/rsi_divergence.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --risk-percent 2.0 --stop-atr-multiple 2.5 --tp-sl-ratio 3.0
USAGE:
------
python strategies/rsi_divergence.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]
REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2018-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2023-12-31)
DATABASE PARAMETERS:
------------------
--dbuser, -u    : PostgreSQL username (default: jason)
--dbpass, -pw   : PostgreSQL password (default: fsck)
--dbname, -n    : PostgreSQL database name (default: market_data)
--cash, -c      : Initial cash for the strategy (default: $100,000)
RSI AND DIVERGENCE PARAMETERS:
----------------------------
--rsi-period, -rp        : RSI calculation period (default: 14)
--divergence-lookback, -dl : Periods to look back for divergence (default: 20)
--rsi-oversold, -ro      : RSI oversold level (default: 30)
--rsi-overbought, -rob   : RSI overbought level (default: 70)
--min-rsi-value, -mrv    : Minimum RSI value for bullish divergence (default: 20)
--max-rsi-value, -maxrv  : Maximum RSI value for bearish divergence (default: 80)
TREND CONFIRMATION:
-----------------
--trend-sma, -ts         : SMA period for trend confirmation (default: 50)
--min-trend-strength, -mts : Minimum consecutive bars in trend direction (default: 0)
--use-volume, -uv        : Use volume confirmation for entries (default: False)
EXIT PARAMETERS:
--------------
--exit-rsi-thresh, -ert   : RSI threshold to exit longs (default: 45)
--exit-rsi-thresh-short, -erts : RSI threshold to exit shorts (default: 55)
RISK MANAGEMENT:
--------------
--risk-percent, -rip      : Risk per trade as percentage of portfolio (default: 1.0)
--max-position-size, -mps : Maximum position size as percentage of portfolio (default: 5.0)
--min-stop-distance, -msd : Minimum distance between entry and stop (default: 0.5%)
--stop-atr-multiple, -sam : ATR multiplier for stop loss (default: 2.0)
--atr-period, -ap         : ATR period (default: 14)
--tp-sl-ratio, -tsr       : Take profit to stop loss ratio (default: 2.0)
--trailing-stop-lookback, -tsl : Lookback period for trailing stop in bars (default: 5)
--use-percent-trailing, -upt  : Use percentage-based trailing stop (default: False)
--trailing-percent, -tp   : Trailing stop percentage (default: 2.0)
TRADE SETTINGS:
-------------
--trade-direction, -td    : Trading direction - long_only, short_only, or both (default: long_only)
--allow-margin, -am       : Enable margin trading (default: disabled)
TRADE THROTTLING:
---------------
--trade-throttle-days, -ttd : Minimum days between trades (default: 5)
OTHER:
-----
--plot, -p      : Generate and show a plot of the trading activity
--log-level, -ll : Logging level (debug, info, warning, error) (default: info)
EXAMPLE:
--------
python strategies/rsi_divergence.py --data AAPL --fromdate 2023-01-01 --todate 2023-12-31 --rsi-period 14 --plot
COMMON PARAMETER COMBINATIONS:
---------------------------
1. Long-only trading with conservative risk:
python strategies/rsi_divergence.py --data TSLA --fromdate 2024-01-01 --todate 2024-12-31 --rsi-period 14 --divergence-lookback 25 --trend-sma 50 --rsi-oversold 25 --rsi-overbought 75 --exit-rsi-thresh 60 --risk-percent 0.25 --stop-atr-multiple 2.0 --tp-sl-ratio 2.5 --trailing-stop-lookback 10 --trade-throttle-days 5 --trade-direction long_only --max-position-size 5.0 --min-stop-distance 0.5
2. Both long and short trading (no margin):
python strategies/rsi_divergence.py --data TSLA --fromdate 2024-01-01 --todate 2024-12-31 --rsi-period 14 --divergence-lookback 25 --trend-sma 50 --exit-rsi-thresh 60 --exit-rsi-thresh-short 40 --trade-direction both --max-position-size 3.0"""

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


class RSIDivergenceStrategy(bt.Strategy, TradeThrottling):
    """RSI Divergence Strategy for Backtrader
This strategy identifies and trades on RSI divergences:
- Bullish divergence: Price makes a lower low while RSI makes a higher low (oversold)
- Bearish divergence: Price makes a higher high while RSI makes a lower high (overbought)
Additional filters include RSI overbought/oversold levels and moving average trend confirmation."""

    params = (
        ("rsi_period", 14),  # RSI lookback period
        ("divergence_lookback", 20),  # Periods to look back for divergence
        ("trend_sma_period", 50),  # SMA period for trend direction
        (
            "min_trend_strength",
            0,
        ),  # Minimum consecutive bars in trend direction
        ("rsi_oversold", 30),  # RSI oversold threshold
        ("rsi_overbought", 70),  # RSI overbought threshold
        ("min_rsi_value", 20),  # Minimum RSI value for bullish divergence
        ("max_rsi_value", 80),  # Maximum RSI value for bearish divergence
        ("use_volume", False),  # Whether to use volume confirmation for entries
        ("risk_percent", 1.0),  # Risk per trade as percentage of portfolio
        # Maximum position size as percentage of portfolio
        ("max_position_size", 5.0),
        (
            "min_stop_distance",
            0.5,
        ),  # Minimum distance between entry and stop as percentage
        ("stop_atr_multiple", 2.0),  # ATR multiplier for stop loss
        ("atr_period", 14),  # ATR period
        ("tp_sl_ratio", 2.0),  # Take profit to stop loss ratio
        ("exit_rsi_thresh", 45),  # Exit long when RSI goes above this
        ("exit_rsi_thresh_short", 55),  # Exit short when RSI falls below this
        ("trade_throttle_days", 5),  # Minimum days between trades
        ("log_level", "info"),  # Logging level (debug, info, warning, error)
        ("trailing_stop_lookback", 5),  # Lookback period for trailing stop
        (
            "use_percent_trailing",
            False,
        ),  # Whether to use percentage-based trailing stop
        ("trailing_percent", 2.0),  # Trailing stop percentage
        (
            "trade_direction",
            "long_only",
        ),  # Trade direction: 'long_only', 'short_only', or 'both'
        ("allow_margin", False),  # Whether to allow margin trading
    )

    def __init__(self):
        """Initialize the strategy"""
        # Store initial cash for drawdown calculation
        self.initial_cash = self.broker.getvalue()

        # Flag to suspend trading if max drawdown is exceeded
        self.trading_suspended = False

        # Max allowed drawdown percentage
        self.max_dd_percent = 10.0

        # Maximum number of consecutive losing trades
        self.max_consecutive_losses = 3
        self.current_consecutive_losses = (
            0  # Correctly initialized as instance variable
        )

        # Calculate indicators
        # RSI indicator
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)

        # Trend confirmation SMA
        self.sma = bt.indicators.SMA(self.data.close, period=self.p.trend_sma_period)

        # ATR for stop loss and volatility measurement
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)

        # For storing swing highs/lows
        self.price_highs = []
        self.price_lows = []
        self.rsi_highs = []
        self.rsi_lows = []

        # Divergence detection flags
        self.divergence_bull = False
        self.divergence_bear = False

        # For tracking orders and positions
        self.buy_order = None
        self.sell_order = None
        self.stop_loss = None
        self.take_profit = None
        self.order_price = None
        self.position_size = 0

        # For trade throttling
        self.last_trade_date = None

        # For plotting - removed plot parameter to avoid TypeError
        self.bull_divergence_signal = bt.indicators.Max(0)
        self.bear_divergence_signal = bt.indicators.Max(0)

        self.trailing_stop = None

    def log(self, txt, dt=None, level="info"):
"""Logging function for this strategy

Args::
    txt: 
    dt: (Default value = None)
    level: (Default value = "info")"""
    level: (Default value = "info")"""
        if level == "debug" and self.p.log_level != "debug":
            return

        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}: {txt}")

    def notify_order(self, order):
"""Called when an order is placed, filled, or canceled.

Args::
    order:"""
    order:"""
        # Skip if order is not completed
        if order.status in [order.Submitted, order.Accepted]:
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED, Price: {order.executed.price:.2f}, Size:"
                    f" {order.executed.size}, Cost: {order.executed.value:.2f}, Comm:"
                    f" {order.executed.comm:.2f}"
                )
                self.order_price = order.executed.price
                self.position_size = order.executed.size
                # Set stop loss and take profit on buy
                self.set_exit_orders(order.executed.price, is_buy=True)
                # Update last trade date for throttling
                self.last_trade_date = self.datas[0].datetime.date(0)
            else:
                self.log(
                    f"SELL EXECUTED, Price: {order.executed.price:.2f}, Size:"
                    f" {order.executed.size}, Cost: {order.executed.value:.2f}, Comm:"
                    f" {order.executed.comm:.2f}"
                )
                self.order_price = order.executed.price
                self.position_size = order.executed.size
                # Set stop loss and take profit on sell
                self.set_exit_orders(order.executed.price, is_buy=False)
                # Update last trade date for throttling
                self.last_trade_date = self.datas[0].datetime.date(0)

        # Handle failed or canceled orders
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order Canceled/Margin/Rejected: {order.status}")

        # Reset order references
        if order == self.buy_order:
            self.buy_order = None
        elif order == self.sell_order:
            self.sell_order = None
        elif order == self.stop_loss:
            self.stop_loss = None
        elif order == self.take_profit:
            self.take_profit = None

    def notify_trade(self, trade):
"""Called when a trade is completed.

Args::
    trade:"""
    trade:"""
        if not trade.isclosed:
            return

        self.log(
            f"TRADE COMPLETED: PnL: Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}"
        )

        # Track consecutive losses for risk management
        if trade.pnl < 0:
            self.current_consecutive_losses += 1
            if self.current_consecutive_losses >= self.max_consecutive_losses:
                self.log(
                    f"WARNING: {self.max_consecutive_losses} consecutive losses reached"
                )
        else:
            self.current_consecutive_losses = 0

    def set_exit_orders(self, entry_price, is_buy=True):
"""Set stop loss and take profit orders with improved trailing stop

Args::
    entry_price: 
    is_buy: (Default value = True)"""
    is_buy: (Default value = True)"""
        # Cancel existing exit orders
        self.cancel_exit_orders()

        atr_val = self.atr[0]

        if is_buy:
            # Set stop loss for long positions
            stop_price = entry_price - (atr_val * self.p.stop_atr_multiple)
            profit_target = entry_price + (
                (entry_price - stop_price) * self.p.tp_sl_ratio
            )

            # Make sure stop price isn't too close to entry
            min_stop_distance = entry_price * (self.p.min_stop_distance / 100)
            if (entry_price - stop_price) < min_stop_distance:
                stop_price = entry_price - min_stop_distance
                profit_target = entry_price + (min_stop_distance * self.p.tp_sl_ratio)

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

            # Set trailing stop for long positions based on chosen method
            if self.p.use_percent_trailing:
                # Use percentage-based trailing stop
                self.trailing_stop = self.sell(
                    exectype=bt.Order.StopTrail,
                    trailpercent=self.p.trailing_percent / 100,
                    size=self.position_size,
                )
                self.log(
                    f"Setting percentage trailing stop at {self.p.trailing_percent}%"
                )
            else:
                # Use ATR-based trailing stop
                trail_amount = atr_val
                self.trailing_stop = self.sell(
                    exectype=bt.Order.StopTrail,
                    trailamount=trail_amount,
                    size=self.position_size,
                )
                self.log(
                    f"Setting trailing stop with initial distance of {trail_amount:.2f}"
                )
        else:
            # Set stop loss for short positions
            stop_price = entry_price + (atr_val * self.p.stop_atr_multiple)
            profit_target = entry_price - (
                (stop_price - entry_price) * self.p.tp_sl_ratio
            )

            # Make sure stop price isn't too close to entry
            min_stop_distance = entry_price * (self.p.min_stop_distance / 100)
            if (stop_price - entry_price) < min_stop_distance:
                stop_price = entry_price + min_stop_distance
                profit_target = entry_price - (min_stop_distance * self.p.tp_sl_ratio)

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

            # Set trailing stop for short positions based on chosen method
            if self.p.use_percent_trailing:
                # Use percentage-based trailing stop
                self.trailing_stop = self.buy(
                    exectype=bt.Order.StopTrail,
                    trailpercent=self.p.trailing_percent / 100,
                    size=self.position_size,
                )
                self.log(
                    f"Setting percentage trailing stop at {self.p.trailing_percent}%"
                )
            else:
                # Use ATR-based trailing stop
                trail_amount = atr_val
                self.trailing_stop = self.buy(
                    exectype=bt.Order.StopTrail,
                    trailamount=trail_amount,
                    size=self.position_size,
                )
                self.log(
                    f"Setting trailing stop with initial distance of {trail_amount:.2f}"
                )

    def cancel_exit_orders(self):
        """Cancel stop loss and take profit orders"""
        if self.stop_loss is not None:
            self.cancel(self.stop_loss)
            self.stop_loss = None

        if self.take_profit is not None:
            self.cancel(self.take_profit)
            self.take_profit = None

        if self.trailing_stop is not None:
            self.cancel(self.trailing_stop)
            self.trailing_stop = None

    def calculate_position_size(self, entry_price, stop_price):
"""Conservative position sizing with absolute limits to prevent excessive risk

Args::
    entry_price: 
    stop_price:"""
    stop_price:"""
        # Set an absolute hard maximum number of shares (no matter what)
        absolute_max_shares = 100  # Never trade more than this many shares

        # Calculate risk amount in dollars (triple-check with safety cap)
        max_risk_dollars = 1000  # Never risk more than this amount per trade
        risk_amount = min(
            self.broker.getvalue() * (self.p.risk_percent / 100),
            max_risk_dollars,
        )

        # Double-check that we're not in a drawdown situation
        current_equity = self.broker.getvalue()
        if current_equity < self.initial_cash * 0.95:  # 5% drawdown
            # Reduce risk if in drawdown
            risk_amount = risk_amount * 0.5
            self.log(
                f"Reducing risk due to drawdown. Current equity: {current_equity:.2f}",
                level="info",
            )

        # Calculate distance between entry and stop price
        risk_per_share = abs(entry_price - stop_price)

        # Ensure minimum distance with a fixed dollar amount for safety
        min_distance_dollars = 0.5  # At least 50 cents between entry and stop
        min_distance_pct = entry_price * (self.p.min_stop_distance / 100)
        min_distance = max(min_distance_pct, min_distance_dollars)

        if risk_per_share < min_distance:
            self.log(
                "Stop too close to entry. Using minimum distance of"
                f" {min_distance:.2f}",
                level="warning",
            )
            risk_per_share = min_distance

        # Calculate position size based on risk with safety check
        if risk_per_share > 0.01:  # Minimum meaningful price distance
            size = risk_amount / risk_per_share
        else:
            self.log("Risk per share too small. Skipping trade.", level="warning")
            return 0  # Skip trade if risk calculation is problematic

        # Cap at percentage of portfolio
        max_pct = self.p.max_position_size / 100
        cash_available = (
            self.broker.getcash() * 0.95
        )  # Use only 95% of available cash for safety
        percent_cap = min(cash_available * max_pct / entry_price, absolute_max_shares)

        if size > percent_cap:
            self.log(
                f"Position size reduced from {size:.0f} to {percent_cap:.0f} to respect"
                " position limits",
                level="info",
            )
            size = percent_cap

        # Final sanity check - absolute cap
        size = min(size, absolute_max_shares)

        # Make sure we're not trading zero shares
        if size < 1:
            self.log(
                "Calculated position size too small. Skipping trade.",
                level="warning",
            )
            return 0

        # Return integer number of shares
        return int(size)

    def get_safe_price_value(self, idx=0):
"""Safely get price values without risk of index errors

Args::
    idx: (Default value = 0)"""
    idx: (Default value = 0)"""
        try:
            return self.data.close[idx]
        except IndexError:
            return None

    def get_safe_rsi_value(self, idx=0):
"""Safely get RSI values without risk of index errors

Args::
    idx: (Default value = 0)"""
    idx: (Default value = 0)"""
        try:
            return self.rsi[idx]
        except IndexError:
            return None

    def is_local_price_minimum(self):
        """Check if the previous bar formed a local price minimum"""
        # Need at least 3 bars
        if len(self.data) < 3:
            return False

        # Get values safely
        current = self.get_safe_price_value(0)
        prev = self.get_safe_price_value(1)
        prev2 = self.get_safe_price_value(2)

        if None in (current, prev, prev2):
            return False

        # Check for local minimum at previous bar
        return prev2 > prev and prev < current

    def is_local_price_maximum(self):
        """Check if the previous bar formed a local price maximum"""
        # Need at least 3 bars
        if len(self.data) < 3:
            return False

        # Get values safely
        current = self.get_safe_price_value(0)
        prev = self.get_safe_price_value(1)
        prev2 = self.get_safe_price_value(2)

        if None in (current, prev, prev2):
            return False

        # Check for local maximum at previous bar
        return prev2 < prev and prev > current

    def is_local_rsi_minimum(self):
        """Check if the previous bar formed a local RSI minimum"""
        # Need at least 3 bars
        if len(self.data) < 3:
            return False

        # Get values safely
        current = self.get_safe_rsi_value(0)
        prev = self.get_safe_rsi_value(1)
        prev2 = self.get_safe_rsi_value(2)

        if None in (current, prev, prev2):
            return False

        # Check for local minimum at previous bar
        return prev2 > prev and prev < current

    def is_local_rsi_maximum(self):
        """Check if the previous bar formed a local RSI maximum"""
        # Need at least 3 bars
        if len(self.data) < 3:
            return False

        # Get values safely
        current = self.get_safe_rsi_value(0)
        prev = self.get_safe_rsi_value(1)
        prev2 = self.get_safe_rsi_value(2)

        if None in (current, prev, prev2):
            return False

        # Check for local maximum at previous bar
        return prev2 < prev and prev > current

    def find_divergences(self):
        """Find price/RSI divergences with improved reliability"""
        # Reset divergence flags
        self.divergence_bull = False
        self.divergence_bear = False

        try:
            # Check for new price highs/lows to track
            if self.is_local_price_minimum():
                # Add new price low with corresponding RSI value
                price_low = self.data.low[1]  # Previous bar's low
                rsi_val = self.rsi[1]  # RSI at the same point

                # Add to tracking lists
                self.price_lows.append((len(self) - 1, price_low, rsi_val))

                # Trim lists to maintain lookback period only
                max_lookback = self.p.divergence_lookback
                if len(self.price_lows) > max_lookback:
                    self.price_lows = self.price_lows[-max_lookback:]

            if self.is_local_price_maximum():
                # Add new price high with corresponding RSI value
                price_high = self.data.high[1]  # Previous bar's high
                rsi_val = self.rsi[1]  # RSI at the same point

                # Add to tracking lists
                self.price_highs.append((len(self) - 1, price_high, rsi_val))

                # Trim lists to maintain lookback period only
                max_lookback = self.p.divergence_lookback
                if len(self.price_highs) > max_lookback:
                    self.price_highs = self.price_highs[-max_lookback:]

            # Bullish Divergence: Price lower low but RSI higher low (in oversold territory)
            # Need at least 2 lows to compare with stricter criteria
            if len(self.price_lows) >= 2:
                # Get the two most recent lows
                _, price_low1, rsi_low1 = self.price_lows[-1]
                _, price_low2, rsi_low2 = self.price_lows[-2]

                # Check if RSI is in oversold territory for the most recent low
                oversold_condition = rsi_low1 < self.p.rsi_oversold

                # Require a more significant price difference (at least 3%)
                price_diff_pct = 100 * abs(price_low1 - price_low2) / price_low2
                significant_price_diff = price_diff_pct > 3.0

                # Require a more significant RSI difference (at least 5 points)
                significant_rsi_diff = abs(rsi_low1 - rsi_low2) > 5.0

                # Detect bullish divergence with stricter criteria
                if (
                    price_low1 < price_low2  # Price made lower low
                    and rsi_low1 > rsi_low2  # RSI made higher low
                    and oversold_condition  # RSI is in oversold territory
                    and significant_price_diff  # Price difference is significant
                    and significant_rsi_diff
                ):  # RSI difference is significant
                    self.divergence_bull = True
                    self.log(
                        "Strong bullish divergence detected: Price"
                        f" {price_low2:.2f}->{price_low1:.2f}, RSI"
                        f" {rsi_low2:.2f}->{rsi_low1:.2f}",
                        level="info",
                    )

            # Bearish Divergence: Price higher high but RSI lower high (in overbought territory)
            # Need at least 2 highs to compare with stricter criteria
            if len(self.price_highs) >= 2:
                # Get the two most recent highs
                _, price_high1, rsi_high1 = self.price_highs[-1]
                _, price_high2, rsi_high2 = self.price_highs[-2]

                # Check if RSI is in overbought territory for the most recent
                # high
                overbought_condition = rsi_high1 > self.p.rsi_overbought

                # Require a more significant price difference (at least 3%)
                price_diff_pct = 100 * abs(price_high1 - price_high2) / price_high2
                significant_price_diff = price_diff_pct > 3.0

                # Require a more significant RSI difference (at least 5 points)
                significant_rsi_diff = abs(rsi_high1 - rsi_high2) > 5.0

                # Detect bearish divergence with stricter criteria
                if (
                    price_high1 > price_high2  # Price made higher high
                    and rsi_high1 < rsi_high2  # RSI made lower high
                    and overbought_condition  # RSI is in overbought territory
                    and significant_price_diff  # Price difference is significant
                    and significant_rsi_diff
                ):  # RSI difference is significant
                    self.divergence_bear = True
                    self.log(
                        "Strong bearish divergence detected: Price"
                        f" {price_high2:.2f}->{price_high1:.2f}, RSI"
                        f" {rsi_high2:.2f}->{rsi_high1:.2f}",
                        level="info",
                    )

        except Exception as e:
            # If there's any error in divergence detection, log it and continue
            # without signal
            self.log(
                f"Error in divergence detection: {str(e)}",
                level="warning",
            )
            self.divergence_bull = False
            self.divergence_bear = False

    def next(self):
        """Main strategy logic with improved risk management"""
        # Skip if any order is pending
        if self.buy_order or self.sell_order:
            return

        # Check for maximum drawdown exceeded
        current_value = self.broker.getvalue()
        drawdown_pct = 100 * (1 - current_value / self.initial_cash)

        if drawdown_pct > self.max_dd_percent:
            # Close all positions and stop trading
            if self.position:
                self.close()
            if not self.trading_suspended:
                self.log(
                    f"TRADING SUSPENDED: Maximum drawdown of {drawdown_pct:.2f}%"
                    " exceeded",
                    level="warning",
                )
            self.trading_suspended = True
            return

        # Additional check for negative equity - emergency stop
        if current_value <= 0:
            if not self.trading_suspended:
                self.log("EMERGENCY STOP: Negative equity detected", level="warning")
            self.trading_suspended = True
            return

        # Skip if trading is suspended due to risk management
        if self.trading_suspended:
            return

        # Reset plotting signals
        self.bull_divergence_signal[0] = float("nan")
        self.bear_divergence_signal[0] = float("nan")

        # Need enough bars for indicators before we can analyze
        min_bars_needed = self.p.rsi_period + 5
        if len(self) <= min_bars_needed:
            return

        # Find divergences safely
        self.find_divergences()

        # Current price and indicators
        price = self.data.close[0]
        current_rsi = self.rsi[0]

        # If we are in a position, check for exit conditions
        if self.position:
            # Exit on first sign of weakness
            if self.position.size > 0 and (
                current_rsi > self.p.exit_rsi_thresh
                or self.data.close[0] < self.data.low[1]
            ):
                self.cancel_exit_orders()
                self.close()
                self.log("EXIT LONG: RSI moved above exit threshold")
                return

            # Early exit for short positions
            elif self.position.size < 0 and current_rsi < self.p.exit_rsi_thresh_short:
                self.cancel_exit_orders()
                self.close()
                self.log("EXIT SHORT: RSI moved below exit threshold")
                return

            # Update trailing stop if needed and it exists
            if not self.p.use_percent_trailing and self.trailing_stop is not None:
                try:
                    if self.position.size > 0:  # Long position
                        # Update stop to the low of the past N bars
                        stop_price = min(
                            self.data.low.get(size=self.p.trailing_stop_lookback)
                        )
                        distance = self.data.close[0] - stop_price
                        if distance > 0:  # Only update if it would tighten the stop
                            self.trailing_stop.trailamount = distance
                    else:  # Short position
                        # Update stop to the high of the past N bars
                        stop_price = max(
                            self.data.high.get(size=self.p.trailing_stop_lookback)
                        )
                        distance = stop_price - self.data.close[0]
                        if distance > 0:  # Only update if it would tighten the stop
                            self.trailing_stop.trailamount = distance
                except Exception as e:
                    self.log(
                        f"Error updating trailing stop: {str(e)}",
                        level="warning",
                    )
                    # If there's an error, reset the trailing stop to avoid
                    # further issues
                    if self.trailing_stop is not None:
                        self.cancel(self.trailing_stop)
                        self.trailing_stop = None

            return

        # ENTRY CONDITIONS

        # Check if we can trade now (throttling)
        if not self.can_trade_now():
            return

        # Accessing previous price safely to check crossovers
        prev_price = self.get_safe_price_value(1)
        if prev_price is None:
            return

        # Check for trend strength if required
        trend_strength_met = True
        if self.p.min_trend_strength > 0:
            # Count consecutive bars above/below SMA
            count_above_sma = 0
            count_below_sma = 0

            for i in range(self.p.min_trend_strength):
                if i >= len(self):
                    trend_strength_met = False
                    break

                if self.data.close[-i] > self.sma[-i]:
                    count_above_sma += 1
                elif self.data.close[-i] < self.sma[-i]:
                    count_below_sma += 1

            # For long entries, need enough consecutive bars above SMA
            # For short entries, need enough consecutive bars below SMA
            if (
                self.p.trade_direction in ["long_only", "both"]
                and count_above_sma < self.p.min_trend_strength
            ):
                trend_strength_met = False
            elif (
                self.p.trade_direction in ["short_only", "both"]
                and count_below_sma < self.p.min_trend_strength
            ):
                trend_strength_met = False

        # Volume confirmation if required
        volume_confirmed = True
        if self.p.use_volume:
            # Simple volume confirmation: current volume above 20-day average
            avg_volume = bt.indicators.SMA(self.data.volume, period=20)
            volume_confirmed = self.data.volume[0] > avg_volume[0]

        # Bullish divergence signal - only if long trades are allowed
        if (
            self.divergence_bull
            and self.p.trade_direction in ["long_only", "both"]
            and trend_strength_met
            and volume_confirmed
            and current_rsi >= self.p.min_rsi_value
        ):  # Apply minimum RSI threshold
            # Confirm with trend (uptrend or price crossing above SMA)
            trend_up = price > self.sma[0]
            price > self.sma[0] and prev_price < self.sma[0]

            # Add confirmation bar requirement
            rsi_moving_favorably = (
                current_rsi > rsi_low1 + 3.0
            )  # RSI moving up after bullish divergence
            # Price moving up
            price_confirming = self.data.close[0] > self.data.close[1]

            # Only enter if we have confirmation
            if (
                trend_up
                and rsi_moving_favorably
                and price_confirming
                and volume_confirmed
            ):
                # Calculate stop loss based on ATR
                stop_price = price - (self.atr[0] * self.p.stop_atr_multiple)

                # Ensure minimum stop distance
                min_stop_distance = price * (self.p.min_stop_distance / 100)
                if (price - stop_price) < min_stop_distance:
                    stop_price = price - min_stop_distance

                # Calculate position size with safety checks
                size = self.calculate_position_size(price, stop_price)

                # Only proceed if we have a valid position size
                if size > 0:
                    # Enter long position
                    self.log(
                        f"BULLISH DIVERGENCE SIGNAL: RSI={current_rsi:.2f}, Size={size}"
                    )
                    self.buy_order = self.buy(size=size)
                    self.bull_divergence_signal[0] = (
                        self.data.low[0] * 0.99
                    )  # For plotting

        # Bearish divergence signal - only if short trades are allowed
        if (
            self.divergence_bear
            and self.p.trade_direction in ["short_only", "both"]
            and trend_strength_met
            and volume_confirmed
            and current_rsi <= self.p.max_rsi_value
        ):  # Apply maximum RSI threshold
            # Confirm with trend (downtrend or price crossing below SMA)
            trend_down = price < self.sma[0]
            sma_cross_down = price < self.sma[0] and prev_price > self.sma[0]

            if trend_down or sma_cross_down:
                # Calculate stop loss based on ATR
                stop_price = price + (self.atr[0] * self.p.stop_atr_multiple)

                # Ensure minimum stop distance
                min_stop_distance = price * (self.p.min_stop_distance / 100)
                if (stop_price - price) < min_stop_distance:
                    stop_price = price + min_stop_distance

                # Calculate position size with safety checks
                size = self.calculate_position_size(price, stop_price)

                # Only proceed if we have a valid position size
                if size > 0:
                    # Enter short position
                    self.log(
                        f"BEARISH DIVERGENCE SIGNAL: RSI={current_rsi:.2f}, Size={size}"
                    )
                    self.sell_order = self.sell(size=size)
                    self.bear_divergence_signal[0] = (
                        self.data.high[0] * 1.01
                    )  # For plotting

    def stop(self):
        """Called when backtest is complete"""
        self.log("RSI Divergence Strategy completed")
        self.log(f"Final Portfolio Value: {self.broker.getvalue():.2f}")

        # Add a note about market conditions
        self.log("NOTE: This strategy performs best in trending markets with pullbacks")
        self.log("      where divergences signal potential trend resumption")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="RSI Divergence Strategy with data from PostgreSQL database",
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
        default="2018-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        default="2023-12-31",
        help="Ending date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--cash", "-c", default=100000.0, type=float, help="Starting cash"
    )

    # RSI and Divergence parameters
    parser.add_argument(
        "--rsi-period",
        "-rp",
        default=14,
        type=int,
        help="RSI calculation period",
    )

    parser.add_argument(
        "--divergence-lookback",
        "-dl",
        default=20,
        type=int,
        help="Periods to look back for divergence",
    )

    parser.add_argument(
        "--rsi-oversold",
        "-ro",
        default=30,
        type=int,
        help="RSI oversold threshold",
    )

    parser.add_argument(
        "--rsi-overbought",
        "-rob",
        default=70,
        type=int,
        help="RSI overbought threshold",
    )

    parser.add_argument(
        "--min-rsi-value",
        "-mrv",
        default=20,
        type=int,
        help="Minimum RSI value for bullish divergence",
    )

    parser.add_argument(
        "--max-rsi-value",
        "-maxrv",
        default=80,
        type=int,
        help="Maximum RSI value for bearish divergence",
    )

    # Trend confirmation
    parser.add_argument(
        "--trend-sma",
        "-ts",
        default=50,
        type=int,
        help="SMA period for trend confirmation",
    )

    parser.add_argument(
        "--min-trend-strength",
        "-mts",
        default=0,
        type=int,
        help="Minimum consecutive bars in trend direction",
    )

    parser.add_argument(
        "--use-volume",
        "-uv",
        action="store_true",
        help="Use volume confirmation for entries",
    )

    # Exit parameters
    parser.add_argument(
        "--exit-rsi-thresh",
        "-ert",
        default=45,
        type=int,
        help="RSI threshold to exit longs",
    )

    parser.add_argument(
        "--exit-rsi-thresh-short",
        "-erts",
        default=55,
        type=int,
        help="RSI threshold to exit shorts",
    )

    # Risk management parameters
    parser.add_argument(
        "--risk-percent",
        "-rip",
        default=1.0,
        type=float,
        help="Risk per trade as percentage of portfolio",
    )

    parser.add_argument(
        "--max-position-size",
        "-mps",
        default=5.0,
        type=float,
        help="Maximum position size as percentage of portfolio",
    )

    parser.add_argument(
        "--min-stop-distance",
        "-msd",
        default=0.5,
        type=float,
        help="Minimum distance between entry and stop as percentage",
    )

    parser.add_argument(
        "--stop-atr-multiple",
        "-sam",
        default=2.0,
        type=float,
        help="ATR multiplier for stop loss",
    )

    parser.add_argument("--atr-period", "-ap", default=14, type=int, help="ATR period")

    parser.add_argument(
        "--tp-sl-ratio",
        "-tsr",
        default=2.0,
        type=float,
        help="Take profit to stop loss ratio",
    )

    parser.add_argument(
        "--trailing-stop-lookback",
        "-tsl",
        default=5,
        type=int,
        help="Lookback period for trailing stop (bars)",
    )

    parser.add_argument(
        "--use-percent-trailing",
        "-upt",
        action="store_true",
        help="Use percentage-based trailing stop",
    )

    parser.add_argument(
        "--trailing-percent",
        "-tp",
        default=2.0,
        type=float,
        help="Trailing stop percentage",
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

    # Trade direction
    parser.add_argument(
        "--trade-direction",
        "-td",
        default="long_only",
        choices=["long_only", "short_only", "both"],
        help="Trade direction: long_only, short_only, or both",
    )

    parser.add_argument(
        "--allow-margin",
        "-am",
        action="store_true",
        help="Enable margin trading (default: disabled)",
    )

    # Logging level
    parser.add_argument(
        "--log-level",
        "-ll",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging level",
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

    # Add the strategy
    cerebro.addstrategy(
        RSIDivergenceStrategy,
        # RSI parameters
        rsi_period=args.rsi_period,
        divergence_lookback=args.divergence_lookback,
        rsi_oversold=args.rsi_oversold,
        rsi_overbought=args.rsi_overbought,
        min_rsi_value=args.min_rsi_value,
        max_rsi_value=args.max_rsi_value,
        # Trend confirmation
        trend_sma_period=args.trend_sma,
        min_trend_strength=args.min_trend_strength,
        use_volume=args.use_volume,
        # Exit parameters
        exit_rsi_thresh=args.exit_rsi_thresh,
        exit_rsi_thresh_short=args.exit_rsi_thresh_short,
        # Risk management
        risk_percent=args.risk_percent,
        max_position_size=args.max_position_size,
        min_stop_distance=args.min_stop_distance,
        stop_atr_multiple=args.stop_atr_multiple,
        atr_period=args.atr_period,
        tp_sl_ratio=args.tp_sl_ratio,
        # Trailing stop
        trailing_stop_lookback=args.trailing_stop_lookback,
        use_percent_trailing=args.use_percent_trailing,
        trailing_percent=args.trailing_percent,
        # Trade throttling
        trade_throttle_days=args.trade_throttle_days,
        # Trade direction and margin
        trade_direction=args.trade_direction,
        allow_margin=args.allow_margin,
        # Logging
        log_level=args.log_level,
    )

    # Set our desired cash start
    cerebro.broker.setcash(args.cash)

    # Set commission with NO margin
    cerebro.broker.setcommission(commission=0.001, leverage=1.0)

    # Set slippage to simulate real market friction
    cerebro.broker.set_slippage_perc(0.0)

    # Set Cheat on Close for order execution
    cerebro.broker.set_coc(True)

    # Disable margin completely
    # Check margin before submitting orders
    cerebro.broker.set_checksubmit(True)

    # Add standard analyzers
    add_standard_analyzers(cerebro)

    # Print out the starting conditions
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Print strategy configuration
    print("\nStrategy Configuration:")
    print(f"Symbol: {args.data}")
    print(f"Date Range: {args.fromdate} to {args.todate}")
    print(
        f"RSI: Period={args.rsi_period}, Oversold={args.rsi_oversold},"
        f" Overbought={args.rsi_overbought}"
    )
    print(f"      Min Value={args.min_rsi_value}, Max Value={args.max_rsi_value}")
    print(f"Divergence Lookback: {args.divergence_lookback} bars")
    print(f"Trend Confirmation: {args.trend_sma} SMA")
    if args.min_trend_strength > 0:
        print(f"  Minimum Trend Strength: {args.min_trend_strength} bars")
    if args.use_volume:
        print("  Using Volume Confirmation: Yes")

    print("\nExit Parameters:")
    print(f"Long Exit RSI: Above {args.exit_rsi_thresh}")
    print(f"Short Exit RSI: Below {args.exit_rsi_thresh_short}")

    print("\nRisk Management:")
    print(f"Risk Per Trade: {args.risk_percent}%")
    print(f"Max Position Size: {args.max_position_size}%")
    print(f"Min Stop Distance: {args.min_stop_distance}%")
    print(f"Stop Loss: {args.stop_atr_multiple}x ATR")
    print(f"Take Profit: {args.tp_sl_ratio}x Stop Loss Distance")

    print("\nTrailing Stop:")
    if args.use_percent_trailing:
        print(f"Type: Percentage-based ({args.trailing_percent}%)")
    else:
        print(f"Type: Bar-based lookback ({args.trailing_stop_lookback} bars)")

    print("\nTrade Settings:")
    print(f"Direction: {args.trade_direction}")
    print(f"Margin Trading: {'Enabled' if args.allow_margin else 'Disabled'}")
    print(f"Log Level: {args.log_level}")
    if args.trade_throttle_days > 0:
        print(f"Trade Throttling: {args.trade_throttle_days} days between trades")

    print("\n--- Starting Backtest ---\n")
    print(
        "*** IMPORTANT: This strategy performs best in trending markets with"
        " pullbacks ***"
    )
    print("where divergences signal potential trend resumption\n")

    # Run the strategy
    results = cerebro.run()

    # Print final portfolio value
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: ${final_value:.2f}")

    # Print standard performance metrics using standardized function
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
