#!/usr/bin/env python
"""
Volatility Contraction Pattern (VCP) Strategy
=============================================

Description:
-----------
This strategy identifies stocks that are poised for a significant breakout after a period of
decreasing volatility and volume contraction, based on the methodology popularized by Mark Minervini.
The strategy looks for stocks that meet specific criteria indicating potential breakout situations
after a consolidation phase where price movements and trading volumes contract.

Strategy Logic:
--------------
1. PRICE PATTERN: The strategy identifies stocks that have formed a "volatility contraction pattern"
   where price movements become progressively tighter, indicating a potential energy build-up before a breakout.

2. VOLUME PATTERN: Volume should also show contraction during the consolidation phase, followed by
   expansion as the price breaks out.

3. TREND ALIGNMENT: The price must remain above longer-term moving averages (like the 250-day SMA)
   to ensure the stock is in a broader uptrend.

4. LIQUIDITY FILTER: The stock must have adequate liquidity (volume × price > threshold) to ensure
   the positions can be entered and exited efficiently.

5. NARROW PRICE CHANNEL: Recent price action should form a narrow price channel, indicating a tight
   trading range that precedes breakouts.

MARKET CONDITIONS:
----------------
*** THIS STRATEGY IS SPECIFICALLY DESIGNED FOR STOCKS IN BASE FORMATION BEFORE BREAKOUT ***
- PERFORMS BEST: In markets where strong stocks are building bases after prior uptrends
- AVOID USING: During market corrections or in strongly downtrending markets
- IDEAL TIMEFRAMES: Daily charts
- OPTIMAL MARKET CONDITION: Bull markets with sector rotation

The strategy excels when applied to stocks that are already showing relative strength
compared to the broader market and are forming consolidation patterns after prior advances.
It struggles in bear markets or with stocks that lack institutional support.

EXAMPLE COMMANDS:
---------------
1. Standard configuration - default VCP detection:
   python strategies/vol_contraction.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31

2. More sensitive volatility detection - shorter lookback periods:
   python strategies/vol_contraction.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --period-short 8 --period-long 25 --narrow-factor 1.8

3. Higher liquidity threshold - focus on more actively traded stocks:
   python strategies/vol_contraction.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --min-dollar-volume 1000000 --max-position 3.0

4. Trend-focused approach - stronger SMA filters:
   python strategies/vol_contraction.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --sma-short 50 --sma-long 200

5. Conservative risk management - tighter stop loss with trailing protection:
   python strategies/vol_contraction.py --data AAPL --fromdate 2024-01-01 --todate 2024-12-31 --stop-loss 3.0 --trail-stop --trail-percent 3.0 --position-percent 1.5

Usage:
------
python strategies/vol_contraction.py --data SYMBOL [parameters]

Required Arguments:
-----------------
--data, -d            Stock symbol to trade

Optional Arguments:
-----------------
Database Connection:
--dbuser, -u          PostgreSQL username (default: 'jason')
--dbpass, -pw         PostgreSQL password (default: 'fsck')
--dbname, -n          PostgreSQL database name (default: 'market_data')
--fromdate, -f        Start date for data retrieval (default: '2024-01-01')
--todate, -t          End date for data retrieval (default: '2024-12-31')
--cash, -c            Initial cash for backtest (default: 100000.0)

VCP Parameters:
--period-short        Short-term lookback period for volatility (default: 10)
--period-long         Long-term lookback period for volatility (default: 60)
--period-long-discount Discount factor for long period (default: 0.7)
--highest-close       Used in VCP calculation (default: 100)
--mean-vol            Period for volume average calculation (default: 20)

Moving Averages:
--sma-long, -sl       Long-term SMA period for trend identification (default: 250)
--sma-short, -ss      Short-term SMA period for exit signals (default: 60)

Price Channel:
--recent-price-period, -rpp Period for narrow channel calculation (default: 20)
--narrow-factor, -nf  Factor for determining narrow channel (default: 0.7)

Liquidity:
--min-dollar-volume, -mdv Minimum dollar volume for liquidity filter (default: 2000000)

Position Sizing:
--position-percent, -pp Position size as percentage of equity (default: 20.0)
--max-position, -mp   Maximum position size as percentage (default: 95.0)

Risk Management:
--stop-loss, -stl      Stop loss percentage (default: 7.0)
--trailing-stop, -ts  Enable trailing stop loss (default: False)
--trail-percent, -tp  Trailing stop percentage (default: 10.0)

Trade Throttling:
--trade-throttle-days, -ttd Minimum days between trades (default: 5)

Other:
--plot, -pl          Generate and show a plot of the trading activity

Examples:
--------
python strategies/vol_contraction.py --data AAPL --period-short 15 --period-long 50
python strategies/vol_contraction.py --data MSFT --sma-long 200 --sma-short 50 --min-dollar-volume 3000000
"""

import argparse
import datetime
import pandas as pd
import backtrader as bt
import numpy as np
import os
import sys

# Add the parent directory to the path so that 'strategies' can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility functions
from strategies.utils import (
    get_db_data,
    print_performance_metrics,
    TradeThrottling,
    add_standard_analyzers,
)


class StockPriceData(bt.feeds.PandasData):
    """
    Data feed class for stock price data from a Pandas DataFrame
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


class VCPPattern(bt.Indicator):
    """
    Custom indicator to detect Volatility Contraction Patterns (VCP)

    The VCP indicator identifies periods of decreasing volatility and
    potential breakout opportunities.

    Lines:
        - vcp: Value representing the volatility contraction (1 when detected, 0 otherwise)

    Params:
        - period_short: Short-term period for volatility measurement
        - period_long: Long-term period for volatility measurement
        - period_long_discount: Discount factor for long-term volatility
        - highest_close: Lookback period for price high
        - mean_vol: Period for volume average calculation
    """

    lines = ("vcp",)
    params = dict(
        period_short=10,  # Short-term volatility period
        period_long=30,  # Long-term volatility period
        period_long_discount=0.7,  # Discount factor for long volatility
        highest_close=50,  # Lookback for price high
        mean_vol=20,  # Volume average period
    )

    def __init__(self):
        # Add each indicator separately rather than trying to combine them

        # Short-range volatility
        self.short_high = bt.indicators.Highest(
            self.data.high, period=self.p.period_short
        )
        self.short_low = bt.indicators.Lowest(self.data.low, period=self.p.period_short)
        self.short_range = self.short_high - self.short_low

        # Long-range volatility
        self.long_high = bt.indicators.Highest(
            self.data.high, period=self.p.period_long
        )
        self.long_low = bt.indicators.Lowest(self.data.low, period=self.p.period_long)
        self.long_range = self.long_high - self.long_low

        # Highest close
        self.highest_close = bt.indicators.Highest(
            self.data.close, period=self.p.highest_close
        )

        # Volume average
        self.avg_volume = bt.indicators.SimpleMovingAverage(
            self.data.volume, period=self.p.mean_vol
        )

    def next(self):
        # Volatility contraction
        vol_contraction = self.short_range[0] < (
            self.long_range[0] * self.p.period_long_discount
        )

        # Near highest price
        near_high = self.data.close[0] > (self.highest_close[0] * 0.85)

        # Volume less than average
        vol_less_than_avg = self.data.volume[0] < self.avg_volume[0]

        # Set the VCP line based on all conditions
        self.lines.vcp[0] = (
            1.0 if (vol_contraction and near_high and vol_less_than_avg) else 0.0
        )


class VCPStrategy(bt.Strategy, TradeThrottling):
    """
    Volatility Contraction Pattern (VCP) Strategy

    This strategy seeks to identify and trade volatility contraction patterns,
    which often precede significant price breakouts. It combines technical indicators
    with filters for liquidity and trend confirmation.

    ** IMPORTANT: This strategy is specifically designed for stocks forming bases
    before breakouts, typically in bull markets with sector rotation **

    Strategy Logic:
    - Looks for periods of contracting volatility (narrowing price ranges)
    - Confirms pattern with price near recent highs and below-average volume
    - Enters when volatility contraction is detected in an overall uptrend
    - Uses risk-based position sizing to manage exposure
    - Employs trailing stops to protect profits

    Best Market Conditions:
    - Works best in bull markets or strong sectors during consolidation phases
    - Most effective when there's sector rotation driving new leadership
    - Avoid using during market corrections or highly volatile periods
    """

    params = (
        # Pattern detection
        ("period_short", 10),  # Short-term volatility period
        ("period_long", 30),  # Long-term volatility period
        ("period_long_discount", 0.7),  # Discount factor for long volatility
        ("highest_close", 50),  # Lookback for highest close
        ("mean_vol", 20),  # Period for volume moving average
        # Moving averages
        ("sma_long", 250),  # Long-term trend SMA
        ("sma_short", 60),  # Short-term trend SMA
        # Narrow channel configuration
        ("recent_price_period", 15),  # Period for checking recent high/low
        ("narrow_factor", 2.0),  # Factor for channel narrowness
        # Entry and exit parameters
        ("stop_loss", 5.0),  # Stop loss percentage
        ("trail_stop", True),  # Use trailing stop
        ("trail_percent", 5.0),  # Trailing stop percentage
        # Risk management
        ("position_percent", 2.0),  # Percentage of portfolio per position
        ("max_position", 5.0),  # Maximum position size as percentage
        ("min_dollar_volume", 500000),  # Minimum dollar volume for liquidity
        # Trade throttling
        ("trade_throttle_days", 5),  # Minimum days between trades
        # Logging
        ("print_log", False),  # Print log to console
    )

    def log(self, txt, dt=None, doprint=False):
        """
        Logging function for the strategy
        """
        if self.p.print_log or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()}: {txt}")

    def __init__(self):
        # Keep references to price and volume data
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume

        # Order and position tracking
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.stop_price = None
        self.trail_price = None

        # Initialize indicators
        # Custom VCP indicator
        self.vcp = VCPPattern(
            self.datas[0],
            period_short=self.p.period_short,
            period_long=self.p.period_long,
            period_long_discount=self.p.period_long_discount,
            highest_close=self.p.highest_close,
            mean_vol=self.p.mean_vol,
        )

        # Moving averages for trend identification
        self.sma_long = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.p.sma_long
        )

        self.sma_short = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.p.sma_short
        )

        # ATR for volatility and stop loss calculation
        self.atr = bt.indicators.ATR(self.datas[0], period=14)

        # Recent price levels for channel detection
        self.recent_high = bt.indicators.Highest(
            self.datas[0].high, period=self.p.recent_price_period
        )

        self.recent_low = bt.indicators.Lowest(
            self.datas[0].low, period=self.p.recent_price_period
        )

        # For trade throttling
        self.last_trade_date = None

    def notify_order(self, order):
        """Process order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            return

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

                # Set initial stop loss based on ATR or percentage
                self.stop_price = self.buyprice * (1.0 - self.p.stop_loss / 100.0)
                self.log(
                    f"Stop loss set at: {self.stop_price:.2f} ({self.p.stop_loss}%)"
                )

                # Set initial trailing stop if enabled
                if self.p.trail_stop:
                    self.trail_price = self.buyprice * (
                        1.0 - self.p.trail_percent / 100.0
                    )
                    self.log(
                        "Trailing stop set at:"
                        f" {self.trail_price:.2f} ({self.p.trail_percent}%)"
                    )

                # Update last trade date for throttling
                self.last_trade_date = self.datas[0].datetime.date(0)

            else:
                self.log(
                    f"SELL EXECUTED: Price: {order.executed.price:.2f}, "
                    f"Size: {order.executed.size}, "
                    f"Cost: {order.executed.value:.2f}, "
                    f"Comm: {order.executed.comm:.2f}"
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order {order.Status[order.status]}")

        self.order = None

    def notify_trade(self, trade):
        """Process trade notifications"""
        if not trade.isclosed:
            return

        self.log(f"TRADE P/L: GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")

    def calculate_position_size(self):
        """Calculate position size based on risk percentage"""
        current_price = self.dataclose[0]
        value = self.broker.getvalue()
        cash = self.broker.getcash()

        # Calculate stop loss price
        stop_price = current_price * (1.0 - self.p.stop_loss / 100.0)

        # Calculate risk amount based on portfolio value
        risk_amount = value * (self.p.position_percent / 100)

        # Calculate risk per share
        risk_per_share = current_price - stop_price

        # Calculate position size based on risk
        if risk_per_share > 0:
            size = int(risk_amount / risk_per_share)

            # Ensure we don't exceed maximum percentage of available cash
            max_size = int((cash * self.p.max_position / 100) / current_price)
            size = min(size, max_size)

            return size

        return 0

    def is_narrow_channel(self):
        """
        Determine if the price is in a narrow channel
        """
        if len(self) <= self.p.recent_price_period:
            return False

        # Calculate channel width as a percentage of price
        channel_high = self.recent_high[0]
        channel_low = self.recent_low[0]
        channel_pct = (channel_high - channel_low) / self.dataclose[0]

        # Channel is narrow if it's less than X * ATR / price
        return channel_pct < (self.atr[0] * self.p.narrow_factor / self.dataclose[0])

    def is_sufficient_liquidity(self):
        """Check if the stock has sufficient dollar volume"""
        dollar_volume = self.dataclose[0] * self.datavolume[0]
        return dollar_volume >= self.p.min_dollar_volume

    def is_uptrend(self):
        """Determine if the stock is in an uptrend"""
        if len(self) <= self.p.sma_long:
            return False

        # Basic uptrend condition: price > sma and shorter sma > longer sma
        return (
            self.dataclose[0] > self.sma_long[0]
            and self.sma_short[0] > self.sma_long[0]
        )

    def next(self):
        """Main strategy logic executed for each bar"""
        # Skip if an order is pending
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # Check for entry signal

            # Check if we can trade based on throttling rules
            if not self.can_trade_now():
                return

            # Check for VCP pattern
            if self.vcp[0] == 1.0:
                # Verify additional conditions
                if (
                    self.is_uptrend()
                    and self.is_narrow_channel()
                    and self.is_sufficient_liquidity()
                ):

                    # Calculate position size
                    size = self.calculate_position_size()

                    if size > 0:
                        self.log(f"BUY CREATE: {self.dataclose[0]:.2f}, Size: {size}")
                        self.order = self.buy(size=size)

        else:
            # Check for exit conditions if we have a position

            # Check for stop loss hit
            if self.datalow[0] <= self.stop_price:
                self.log(f"SELL CREATE (Stop Loss): {self.dataclose[0]:.2f}")
                self.order = self.sell()
                return

            # Check trailing stop if enabled
            if self.p.trail_stop and self.trail_price is not None:
                # Update trail price if price moved higher
                if self.datahigh[0] > self.buyprice:
                    new_trail_price = self.datahigh[0] * (
                        1.0 - self.p.trail_percent / 100.0
                    )
                    if new_trail_price > self.trail_price:
                        self.trail_price = new_trail_price
                        self.log(f"Trailing stop updated to: {self.trail_price:.2f}")

                # Check if trailing stop is hit
                if self.datalow[0] <= self.trail_price:
                    self.log(f"SELL CREATE (Trailing Stop): {self.dataclose[0]:.2f}")
                    self.order = self.sell()
                    return

            # Exit if price breaks below the short-term moving average
            if self.dataclose[0] < self.sma_short[0]:
                self.log(f"SELL CREATE (MA Crossdown): {self.dataclose[0]:.2f}")
                self.order = self.sell()

    def stop(self):
        """Called when backtest is complete"""
        self.log("VCP Strategy completed", doprint=True)
        self.log(f"Final Portfolio Value: {self.broker.getvalue():.2f}", doprint=True)

        # Add a note about market conditions
        self.log(
            "NOTE: This strategy is designed for stocks forming bases before breakouts",
            doprint=True,
        )
        self.log(
            "      It works best in bull markets with sector rotation", doprint=True
        )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Volatility Contraction Pattern Strategy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Basic parameters
    parser.add_argument("--data", "-d", required=True, help="Stock symbol to trade")

    parser.add_argument("--dbuser", "-u", default="jason", help="PostgreSQL username")

    parser.add_argument("--dbpass", "-pw", default="fsck", help="PostgreSQL password")

    parser.add_argument(
        "--dbname", "-n", default="market_data", help="PostgreSQL database name"
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        default="2024-01-01",
        help="Start date for data retrieval (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--todate",
        "-t",
        default="2024-12-31",
        help="End date for data retrieval (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--cash", "-c", type=float, default=100000.0, help="Initial cash for backtest"
    )

    # VCP parameters
    parser.add_argument(
        "--period-short",
        type=int,
        default=10,
        help="Short-term lookback period for volatility",
    )

    parser.add_argument(
        "--period-long",
        type=int,
        default=60,
        help="Long-term lookback period for volatility",
    )

    parser.add_argument(
        "--period-long-discount",
        type=float,
        default=0.7,
        help="Discount factor for long period",
    )

    parser.add_argument(
        "--highest-close",
        type=int,
        default=100,
        help="Lookback period for highest close",
    )

    parser.add_argument(
        "--mean-vol", type=int, default=20, help="Period for volume average calculation"
    )

    # Moving average parameters
    parser.add_argument(
        "--sma-long",
        "-sl",
        type=int,
        default=250,
        help="Long-term SMA period for trend identification",
    )

    parser.add_argument(
        "--sma-short",
        "-ss",
        type=int,
        default=60,
        help="Short-term SMA period for exit signals",
    )

    # Price channel parameters
    parser.add_argument(
        "--recent-price-period",
        "-rpp",
        type=int,
        default=20,
        help="Period for narrow channel calculation",
    )

    parser.add_argument(
        "--narrow-factor",
        "-nf",
        type=float,
        default=0.7,
        help="Factor for determining narrow channel",
    )

    # Liquidity filter
    parser.add_argument(
        "--min-dollar-volume",
        "-mdv",
        type=float,
        default=2000000,
        help="Minimum dollar volume for liquidity filter",
    )

    # Position sizing
    parser.add_argument(
        "--position-percent",
        "-pp",
        type=float,
        default=20.0,
        help="Position size as percentage of equity",
    )

    parser.add_argument(
        "--max-position",
        "-mp",
        type=float,
        default=95.0,
        help="Maximum position size as percentage",
    )

    # Risk management
    parser.add_argument(
        "--stop-loss", "-stl", type=float, default=7.0, help="Stop loss percentage"
    )

    parser.add_argument(
        "--trailing-stop", "-ts", action="store_true", help="Enable trailing stop loss"
    )

    parser.add_argument(
        "--trail-percent",
        "-tp",
        type=float,
        default=10.0,
        help="Trailing stop percentage",
    )

    # Trade throttling
    parser.add_argument(
        "--trade-throttle-days",
        "-ttd",
        type=int,
        default=5,
        help="Minimum days between trades",
    )

    # Other parameters
    parser.add_argument(
        "--plot",
        "-pl",
        action="store_true",
        help="Generate plot of the trading activity",
    )

    return parser.parse_args()


def main():
    """
    Main function to run the strategy
    """
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
        VCPStrategy,
        # VCP parameters
        period_short=args.period_short,
        period_long=args.period_long,
        period_long_discount=args.period_long_discount,
        highest_close=args.highest_close,
        mean_vol=args.mean_vol,
        # Moving average parameters
        sma_long=args.sma_long,
        sma_short=args.sma_short,
        # Price channel parameters
        recent_price_period=args.recent_price_period,
        narrow_factor=args.narrow_factor,
        # Liquidity filter
        min_dollar_volume=args.min_dollar_volume,
        # Position sizing
        position_percent=args.position_percent,
        max_position=args.max_position,
        # Risk management
        stop_loss=args.stop_loss,
        trail_stop=args.trailing_stop,
        trail_percent=args.trail_percent,
        # Trade throttling
        trade_throttle_days=args.trade_throttle_days,
        # Other parameters
        print_log=True,
    )

    # Set our desired cash start
    cerebro.broker.setcash(args.cash)

    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)

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
    print(f"- Short Period: {args.period_short} days")
    print(f"- Long Period: {args.period_long} days")
    print(f"- Stop Loss: {args.stop_loss}%")
    print(f"- Position Size: {args.position_percent}% of portfolio")
    print(f"- Trade Throttle: {args.trade_throttle_days} days")

    print("\n--- Starting Backtest ---\n")

    # Run over everything
    results = cerebro.run()

    # Print out the final result
    print("\n--- Backtest Results ---\n")
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():.2f}")

    # Use the centralized performance metrics function
    print_performance_metrics(cerebro, results)

    # Plot if requested
    if args.plot:
        cerebro.plot(style="candle", barup="green", bardown="red")


if __name__ == "__main__":
    main()
