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
"""FIBONACCI RETRACEMENT PULLBACK STRATEGY WITH POSTGRESQL DATABASE - (fib-pullback)
=============================================================================
This strategy implements a Fibonacci retracement pullback trading system that identifies
strong uptrends and enters long positions when price pulls back to key Fibonacci levels.
STRATEGY LOGIC:
--------------
1. Trend Identification:
- Uses RSI to confirm uptrend strength (RSI > 50 for uptrend)
- Requires a minimum price increase over N periods
2. Fibonacci Levels:
- Calculates retracement levels at 38.2%, 50%, and 61.8%
- Uses recent swing high and low points
3. Entry Conditions:
- Price pulls back to a Fibonacci level
- RSI shows oversold conditions (< 30)
- Volume confirms the bounce
4. Exit Conditions:
- Stop loss below the retracement level
- Take profit at previous swing high
- Trailing stop option available
MARKET CONDITIONS:
----------------
*** SPECIFICALLY DESIGNED FOR PULLBACKS WITHIN ESTABLISHED UPTRENDS ***
- PERFORMS BEST: In bull markets with clear pullbacks to support levels
- AVOID USING: In bear markets or during major market corrections
- IDEAL TIMEFRAMES: 1-hour, 4-hour, and daily charts
- OPTIMAL MARKET CONDITION: Stocks showing strong momentum with healthy pullbacks
The strategy is designed to catch pullbacks to key support levels within uptrends.
It will struggle in choppy markets or during major corrections, as it may enter
positions prematurely. The strategy performs best when price respects Fibonacci
retracement levels and has strong rebounds from these levels with volume confirmation.
RISK MANAGEMENT CONSIDERATIONS:
-----------------------------
- Consider wider stop losses during higher market volatility
- In choppy markets, more false signals will be generated
- Using the volume confirmation filter helps avoid false breakouts
- The strategy might enter too early during corrections, so risk management is essential
FIBONACCI RETRACEMENTS:
---------------------
Fibonacci retracement levels are horizontal lines that indicate potential support and
resistance levels where price might reverse direction. They are based on Fibonacci numbers
and the key levels used in this strategy are:
- 38.2% retracement
- 50.0% retracement
- 61.8% retracement
These levels often act as support during pullbacks in uptrends.
USAGE:
------
python strategies/fibonacci_retracement_pullback.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]
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
TREND PARAMETERS:
----------------
--trend-period, -tper     : Period for trend calculation (default: 20)
--trend-strength, -ts   : Minimum price increase % for trend (default: 5.0)
--rsi-period, -rp      : RSI period for trend confirmation (default: 14)
--rsi-upper, -ru       : RSI upper threshold for trend (default: 70)
--rsi-lower, -rl       : RSI lower threshold for entry (default: 30)
FIBONACCI PARAMETERS:
-------------------
--swing-lookback, -swl  : Bars to look back for swing points (default: 50)
--fib-levels, -fl     : Fibonacci levels to use (default: [0.382, 0.5, 0.618])
--bounce-threshold, -bt : Minimum bounce % from level (default: 0.5)
--volume-mult, -vm   : Volume increase factor for confirmation (default: 1.5)
--price-tolerance, -pt  : How close price needs to be to Fibonacci level (%) (default: 0.5)
EXIT PARAMETERS:
--------------
--use-stop, -us      : Use stop loss (default: True)
--stop-pct, -sp      : Stop loss % below entry (default: 2.0)
--target-pct, -tp    : Take profit % above entry (default: 5.0)
--use-trail, -ut  : Use trailing stop (default: False)
--trail-pct, -trp : Trailing stop % (default: 2.0)
POSITION SIZING:
--------------
--risk-percent, -riskp   : Risk percentage per trade (default: 1.0)
--max-position, -mp   : Maximum position size % of equity (default: 20.0)
TRADE THROTTLING:
---------------
--trade-throttle-days, -ttd : Minimum days between trades (default: 1)
OTHER:
-----
--plot, -p          : Generate and show a plot of the trading activity
EXAMPLE:
--------
python strategies/fibonacci_retracement_pullback.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --trend-period 20 --rsi-period 14 --plot"""

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
        ("rsi", "RSI"),
        ("openinterest", None),
    )


class FibonacciLevels(bt.Indicator):
    """Custom indicator to calculate Fibonacci retracement levels"""

    lines = ("fib382", "fib500", "fib618")
    params = (("period", 50),)

    def __init__(self):
        """ """
        super(FibonacciLevels, self).__init__()
        # Set minimum period
        self.addminperiod(self.p.period)

    def next(self):
        """ """
        # Get available bars
        high_array = self.data.high.get(size=self.p.period)
        low_array = self.data.low.get(size=self.p.period)

        # Check if we have enough data
        if len(high_array) > 0 and len(low_array) > 0:
            high = max(high_array)
            low = min(low_array)
            range_ = high - low

            # Calculate Fibonacci levels
            self.lines.fib382[0] = high - (range_ * 0.382)
            self.lines.fib500[0] = high - (range_ * 0.500)
            self.lines.fib618[0] = high - (range_ * 0.618)
        else:
            # Not enough data, set to current price
            self.lines.fib382[0] = self.data.close[0]
            self.lines.fib500[0] = self.data.close[0]
            self.lines.fib618[0] = self.data.close[0]


class FibonacciPullbackStrategy(bt.Strategy, TradeThrottling):
    """Fibonacci Retracement Pullback Strategy
This strategy identifies strong uptrends and enters long positions when price
pulls back to key Fibonacci retracement levels. It uses RSI to confirm trend
direction and oversold conditions, and requires volume confirmation for entries.
The strategy is specifically designed for catching pullbacks in established uptrends.
It will struggle in bear markets or during major corrections."""

    params = (
        # Trend Parameters
        ("trend_period", 20),
        ("trend_strength", 5.0),  # Minimum price increase %
        ("rsi_period", 14),
        ("rsi_upper", 70),
        ("rsi_lower", 30),
        # Fibonacci Parameters
        ("swing_lookback", 50),
        ("fib_levels", [0.382, 0.5, 0.618]),
        ("bounce_threshold", 0.5),  # Minimum bounce %
        ("volume_mult", 1.5),  # Volume increase factor
        (
            "price_tolerance",
            0.5,
        ),  # How close price needs to be to fib level (%)
        # Exit Parameters
        ("use_stop", True),  # Use stop loss
        ("stop_pct", 2.0),  # Stop loss %
        ("target_pct", 5.0),  # Take profit %
        ("use_trail", False),  # Use trailing stop
        ("trail_pct", 2.0),  # Trailing stop %
        # Position Sizing
        ("risk_percent", 1.0),  # Risk percentage per trade
        ("max_position", 20.0),  # Maximum position size % of equity
        # Trade throttling
        ("trade_throttle_days", 1),  # Minimum days between trades
        # Logging
        ("log_level", "info"),  # Logging level: 'debug', 'info'
    )

    def __init__(self):
        """ """
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume

        # Initialize indicators
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)
        self.fib = FibonacciLevels(period=self.p.swing_lookback)
        self.sma = bt.indicators.SMA(period=self.p.trend_period)
        self.atr = bt.indicators.ATR(period=self.p.trend_period)

        # Trading state variables
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.stop_loss = None
        self.take_profit = None
        self.trailing_stop = None

        # Track highest price since entry
        self.highest_price = 0

        # For trade throttling
        self.last_trade_date = None

    def log(self, txt, dt=None, level="info"):
        """Logging function

Args:
    txt: 
    dt: (Default value = None)
    level: (Default value = "info")"""
        if level == "debug" and self.p.log_level != "debug":
            return

        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}: {txt}")

    def notify_order(self, order):
        """Args:
    order:"""
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

                # Set stop loss and take profit
                self.stop_loss = self.buyprice * (1 - self.p.stop_pct / 100)
                self.take_profit = self.buyprice * (1 + self.p.target_pct / 100)
                self.highest_price = self.buyprice

            else:
                self.log(
                    f"SELL EXECUTED: Price: {order.executed.price:.2f}, "
                    f"Size: {order.executed.size}, Cost: {order.executed.value:.2f}, "
                    f"Comm: {order.executed.comm:.2f}"
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None

    def notify_trade(self, trade):
        """Args:
    trade:"""
        if not trade.isclosed:
            return

        self.log(
            f"TRADE COMPLETED: PnL: Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}"
        )

    def is_uptrend(self):
        """Check if we're in an uptrend"""
        # Ensure we have enough data
        if len(self) < self.p.trend_period:
            return False

        # Price above SMA
        price_above_sma = self.dataclose[0] > self.sma[0]

        # RSI confirms uptrend
        rsi_confirms = self.rsi[0] > 50

        # Price increase over period
        start_price = self.dataclose[-self.p.trend_period]
        price_increase = ((self.dataclose[0] - start_price) / start_price) * 100
        strong_trend = price_increase > self.p.trend_strength

        return price_above_sma and rsi_confirms and strong_trend

    def is_pullback(self):
        """Check if we have a valid pullback to Fibonacci level"""
        # Ensure we have enough data
        if len(self) < self.p.swing_lookback:
            return False

        # Check if price is near any Fibonacci level
        for fib_line in [self.fib.fib382, self.fib.fib500, self.fib.fib618]:
            fib_level = fib_line[0]

            # Price should be within tolerance % of Fibonacci level
            price_near_fib = abs(self.dataclose[0] - fib_level) / fib_level < (
                self.p.price_tolerance / 100
            )

            # RSI should be oversold
            rsi_oversold = self.rsi[0] < self.p.rsi_lower

            # Volume should be increasing
            vol_increasing = (
                self.datavolume[0] > self.datavolume[-1] * self.p.volume_mult
            )

            if price_near_fib and rsi_oversold and vol_increasing:
                return True

        return False

    def calculate_position_size(self):
        """Calculate position size based on risk parameters"""
        value = self.broker.getvalue()
        current_price = self.dataclose[0]

        # Calculate position size based on risk percentage
        risk_amount = value * (self.p.risk_percent / 100)
        risk_per_share = current_price * (self.p.stop_pct / 100)

        if risk_per_share > 0:
            size = int(risk_amount / risk_per_share)
        else:
            # Fallback calculation based on max position
            size = int((value * self.p.max_position / 100) / current_price)

        # Make sure we don't exceed maximum position size
        max_size = int(
            (self.broker.getcash() * self.p.max_position / 100) / current_price
        )
        return min(size, max_size)

    def should_exit_trade(self):
        """Determine if we should exit the trade"""
        if not self.position:
            return False

        # Update trailing stop if enabled
        if self.p.use_trail and self.datahigh[0] > self.highest_price:
            self.highest_price = self.datahigh[0]
            self.trailing_stop = self.highest_price * (1 - self.p.trail_pct / 100)

        # Check stop loss
        if self.p.use_stop and self.datalow[0] <= self.stop_loss:
            self.log(
                f"STOP LOSS TRIGGERED: Price: {self.datalow[0]:.2f}, Stop:"
                f" {self.stop_loss:.2f}"
            )
            return True

        # Check take profit
        if self.datahigh[0] >= self.take_profit:
            self.log(
                f"TARGET PROFIT REACHED: Price: {self.datahigh[0]:.2f}, Target:"
                f" {self.take_profit:.2f}"
            )
            return True

        # Check trailing stop
        if self.p.use_trail and self.datalow[0] <= self.trailing_stop:
            self.log(
                f"TRAILING STOP TRIGGERED: Price: {self.datalow[0]:.2f}, Stop:"
                f" {self.trailing_stop:.2f}"
            )
            return True

        return False

    def next(self):
        """ """
        # Check if an order is pending
        if self.order:
            return

        # Debug info
        if len(self) % 10 == 0:
            self.log(
                f"Close: {self.dataclose[0]:.2f}, RSI: {self.rsi[0]:.2f}, "
                f"Fib382: {self.fib.fib382[0]:.2f}, Fib618: {self.fib.fib618[0]:.2f}",
                level="debug",
            )

        # Check if we are in the market
        if not self.position:
            # Check if we can trade now (throttling)
            if not self.can_trade_now():
                return

            # Check for entry conditions
            if self.is_uptrend() and self.is_pullback():
                size = self.calculate_position_size()
                if size > 0:
                    self.log(
                        f"BUY SIGNAL: Price: {self.dataclose[0]:.2f}, Pullback to"
                        " Fibonacci level"
                    )
                    self.order = self.buy(size=size)

                    # Update last trade date for throttling
                    self.last_trade_date = self.datas[0].datetime.date(0)

        else:
            # Check for exit conditions
            if self.should_exit_trade():
                self.log(f"SELL SIGNAL: Price: {self.dataclose[0]:.2f}")
                self.order = self.sell(size=self.position.size)

    def stop(self):
        """Called when backtest is complete"""
        self.log("Fibonacci Retracement Pullback Strategy completed")
        self.log(f"Final Portfolio Value: {self.broker.getvalue():.2f}")

        # Add a note about market conditions
        self.log(
            "NOTE: This strategy is specifically designed for PULLBACKS WITHIN UPTRENDS"
        )
        self.log("      It performs poorly in bear markets or during major corrections")
        self.log(
            "      Ideal conditions: Stocks showing strong momentum with healthy"
            " pullbacks"
        )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Fibonacci Retracement Pullback Strategy",
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
        "--todate",
        "-t",
        default="2024-12-31",
        help="Ending date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--cash", "-c", type=float, default=100000.0, help="Starting cash"
    )

    # Trend parameters
    parser.add_argument(
        "--trend-period",
        "-tper",
        type=int,
        default=20,
        help="Period for trend calculation",
    )
    parser.add_argument(
        "--trend-strength",
        "-ts",
        type=float,
        default=5.0,
        help="Minimum price increase % for trend",
    )
    parser.add_argument(
        "--rsi-period",
        "-rp",
        type=int,
        default=14,
        help="RSI period for trend confirmation",
    )
    parser.add_argument(
        "--rsi-upper", "-ru", type=int, default=70, help="RSI upper threshold"
    )
    parser.add_argument(
        "--rsi-lower", "-rl", type=int, default=30, help="RSI lower threshold"
    )

    # Fibonacci parameters
    parser.add_argument(
        "--swing-lookback",
        "-swl",
        type=int,
        default=50,
        help="Bars to look back for swing points",
    )
    parser.add_argument(
        "--bounce-threshold",
        "-bt",
        type=float,
        default=0.5,
        help="Minimum bounce % from level",
    )
    parser.add_argument(
        "--volume-mult",
        "-vm",
        type=float,
        default=1.5,
        help="Volume increase factor for confirmation",
    )
    parser.add_argument(
        "--price-tolerance",
        "-pt",
        type=float,
        default=0.5,
        help="How close price needs to be to Fibonacci level (%)",
    )

    # Exit parameters
    parser.add_argument(
        "--use-stop",
        "-us",
        action="store_true",
        default=True,
        help="Use stop loss",
    )
    parser.add_argument(
        "--stop-pct",
        "-sp",
        type=float,
        default=2.0,
        help="Stop loss % below entry",
    )
    parser.add_argument(
        "--target-pct",
        "-tp",
        type=float,
        default=5.0,
        help="Take profit % above entry",
    )
    parser.add_argument(
        "--use-trail", "-ut", action="store_true", help="Use trailing stop"
    )
    parser.add_argument(
        "--trail-pct", "-trp", type=float, default=2.0, help="Trailing stop %"
    )

    # Position sizing
    parser.add_argument(
        "--risk-percent",
        "-riskp",
        type=float,
        default=1.0,
        help="Risk percentage per trade",
    )
    parser.add_argument(
        "--max-position",
        "-mp",
        type=float,
        default=20.0,
        help="Maximum position size % of equity",
    )

    # Trade throttling
    parser.add_argument(
        "--trade-throttle-days",
        "-ttd",
        type=int,
        default=1,
        help="Minimum days between trades",
    )

    # Other
    parser.add_argument(
        "--plot",
        "-p",
        action="store_true",
        help="Generate and show a plot of the trading activity",
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

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add the data feed
    cerebro.adddata(data)

    # Add strategy
    cerebro.addstrategy(
        FibonacciPullbackStrategy,
        # Trend parameters
        trend_period=args.trend_period,
        trend_strength=args.trend_strength,
        rsi_period=args.rsi_period,
        rsi_upper=args.rsi_upper,
        rsi_lower=args.rsi_lower,
        # Fibonacci parameters
        swing_lookback=args.swing_lookback,
        bounce_threshold=args.bounce_threshold,
        volume_mult=args.volume_mult,
        price_tolerance=args.price_tolerance,
        # Exit parameters
        use_stop=args.use_stop,
        stop_pct=args.stop_pct,
        target_pct=args.target_pct,
        use_trail=args.use_trail,
        trail_pct=args.trail_pct,
        # Position sizing
        risk_percent=args.risk_percent,
        max_position=args.max_position,
        # Trade throttling
        trade_throttle_days=args.trade_throttle_days,
        # Logging
        log_level="info",
    )

    # Set cash
    cerebro.broker.setcash(args.cash)

    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)

    # Set slippage
    cerebro.broker.set_slippage_perc(0.0)

    # Add the standard analyzers
    add_standard_analyzers(cerebro)

    # Print out the starting conditions
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Print strategy configuration
    print("\nStrategy Configuration:")
    print(f"Symbol: {args.data}")
    print(f"Date Range: {args.fromdate} to {args.todate}")
    print(f"Trend Period: {args.trend_period} bars")
    print(
        f"RSI Parameters: Period={args.rsi_period}, Upper={args.rsi_upper},"
        f" Lower={args.rsi_lower}"
    )
    print(f"Fibonacci Lookback: {args.swing_lookback} bars")
    print(f"Price Tolerance: {args.price_tolerance}%")

    print("\nExit Parameters:")
    if args.use_stop:
        print(f"Stop Loss: {args.stop_pct}%")
    else:
        print("Stop Loss: Disabled")

    print(f"Take Profit: {args.target_pct}%")

    if args.use_trail:
        print(f"Trailing Stop: {args.trail_pct}%")
    else:
        print("Trailing Stop: Disabled")

    print(
        f"\nPosition Sizing: {args.risk_percent}% risk per trade (max"
        f" {args.max_position}%)"
    )

    if args.trade_throttle_days > 0:
        print(f"Trade Throttling: {args.trade_throttle_days} days between trades")

    print("\n--- Starting Backtest ---\n")
    print(
        "*** IMPORTANT: This strategy is specifically designed for PULLBACKS WITHIN"
        " UPTRENDS ***"
    )
    print(
        "It performs poorly in bear markets or during major corrections. Best used with"
        " stocks"
    )
    print(
        "showing strong momentum with healthy pullbacks to key Fibonacci retracement"
        " levels.\n"
    )

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
