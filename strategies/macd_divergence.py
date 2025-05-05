import numpy as np
import pandas as pd
import backtrader as bt
import argparse
import datetime
import os
import sys

# Add the parent directory to the Python path to import shared modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utility functions
from strategies.utils import (
    get_db_data,
    print_performance_metrics,
    TradeThrottling,
    add_standard_analyzers,
)


class MACDDivergenceStrategy(bt.Strategy, TradeThrottling):
    """
    MACD Divergence Strategy

    Identifies and trades on MACD divergences:
    - Bullish divergence: Price makes lower lows while MACD makes higher lows
    - Bearish divergence: Price makes higher highs while MACD makes lower highs

    Strategy Logic:
    - Monitors for divergence between price and MACD
    - Enters when divergence is confirmed by crossover
    - Uses risk-based position sizing and stop loss
    - Implements cool down period to avoid overtrading

    Best Market Conditions:
    - Works best in ranging markets with clear support and resistance levels
    - Avoid using during strong trending markets where indicators may lag
    - Most effective at major market turning points
    """

    params = (
        ("fast_ema", 12),  # Fast EMA period
        ("slow_ema", 26),  # Slow EMA period
        ("signal_period", 9),  # Signal line period
        ("rsi_period", 14),  # RSI period
        ("rsi_upper", 70),  # RSI overbought level
        ("rsi_lower", 30),  # RSI oversold level
        ("risk_pct", 0.02),  # Risk percentage per trade
        ("stop_loss_pct", 0.05),  # Stop loss percentage
        ("take_profit_pct", 0.1),  # Take profit percentage
        ("trade_throttle_days", 5),  # days to wait after a trade
        ("divergence_window", 5),  # Window to look for divergence
    )

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}: {txt}")

    def __init__(self):
        # Initialize indicators
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # MACD
        self.macd = bt.indicators.MACD(
            self.dataclose,
            period_me1=self.params.fast_ema,
            period_me2=self.params.slow_ema,
            period_signal=self.params.signal_period,
        )
        self.macd_line = self.macd.macd
        self.signal_line = self.macd.signal

        # MACD cross signals
        self.macd_cross_above = bt.indicators.CrossOver(
            self.macd_line, self.signal_line
        )
        self.macd_cross_below = bt.indicators.CrossOver(
            self.signal_line, self.macd_line
        )

        # For confirmation
        self.rsi = bt.indicators.RSI(period=self.params.rsi_period)

        # Order and position tracking
        self.order = None
        self.trade_history = []

        # Initialize last trade date for trade throttling
        self.last_trade_date = None

        # For tracking price and MACD values for divergence detection
        self.price_lows = []
        self.price_highs = []
        self.macd_lows = []
        self.macd_highs = []

    def prenext(self):
        self.next()

    def detect_bullish_divergence(self):
        """
        Detect bullish divergence: price makes lower lows while MACD makes higher lows

        Bullish divergence occurs when price makes a lower low but the MACD
        makes a higher low, indicating potential upward momentum reversal.
        """
        if len(self.price_lows) < 2 or len(self.macd_lows) < 2:
            return False

        # Check if price made lower lows
        price_lower_low = self.price_lows[-1] < self.price_lows[-2]

        # Check if MACD made higher lows
        macd_higher_low = self.macd_lows[-1] > self.macd_lows[-2]

        # Additional confirmation: RSI should be in oversold territory
        rsi_oversold = self.rsi[0] < self.params.rsi_lower

        # Calculate divergence strength - a measure of how significant the divergence is
        if price_lower_low and macd_higher_low:
            price_percent_change = (self.price_lows[-1] / self.price_lows[-2] - 1) * 100
            macd_percent_change = (
                (self.macd_lows[-1] / self.macd_lows[-2] - 1) * 100
                if self.macd_lows[-2] != 0
                else 0
            )

            # Strong divergence has a significant price drop and MACD rise
            is_strong_divergence = (
                abs(price_percent_change) > 1.0 and macd_percent_change > 5.0
            )

            # Return true if the divergence is strong or if RSI confirms it
            return is_strong_divergence or (
                price_lower_low and macd_higher_low and rsi_oversold
            )

        return False

    def detect_bearish_divergence(self):
        """
        Detect bearish divergence: price makes higher highs while MACD makes lower highs

        Bearish divergence occurs when price makes a higher high but the MACD
        makes a lower high, indicating potential downward momentum reversal.
        """
        if len(self.price_highs) < 2 or len(self.macd_highs) < 2:
            return False

        # Check if price made higher highs
        price_higher_high = self.price_highs[-1] > self.price_highs[-2]

        # Check if MACD made lower highs
        macd_lower_high = self.macd_highs[-1] < self.macd_highs[-2]

        # Additional confirmation: RSI should be in overbought territory
        rsi_overbought = self.rsi[0] > self.params.rsi_upper

        # Calculate divergence strength - a measure of how significant the divergence is
        if price_higher_high and macd_lower_high:
            price_percent_change = (
                self.price_highs[-1] / self.price_highs[-2] - 1
            ) * 100
            macd_percent_change = (
                (self.macd_highs[-1] / self.macd_highs[-2] - 1) * 100
                if self.macd_highs[-2] != 0
                else 0
            )

            # Strong divergence has a significant price rise and MACD drop
            is_strong_divergence = (
                price_percent_change > 1.0 and abs(macd_percent_change) > 5.0
            )

            # Return true if the divergence is strong or if RSI confirms it
            return is_strong_divergence or (
                price_higher_high and macd_lower_high and rsi_overbought
            )

        return False

    def calculate_position_size(self, stop_price):
        """Calculate position size based on risk percentage"""
        account_value = self.broker.getvalue()
        risk_amount = account_value * self.params.risk_pct
        price_diff = abs(self.dataclose[0] - stop_price)

        if price_diff == 0:  # Avoid division by zero
            return 0

        position_size = risk_amount / price_diff
        return int(position_size)

    def next(self):
        # Skip if an order is pending
        if self.order:
            return

        # Check if we can trade (throttling)
        if not self.can_trade_now():
            return

        # Update our history lists for divergence detection
        # New local minimum in price
        if (
            len(self.data) >= 3
            and self.datalow[-1] < self.datalow[-2]
            and self.datalow[-1] < self.datalow[0]
        ):
            self.price_lows.append(self.datalow[-1])
            self.macd_lows.append(self.macd_line[-1])

            # Keep only the last few values
            if len(self.price_lows) > self.params.divergence_window:
                self.price_lows.pop(0)
                self.macd_lows.pop(0)

        # New local maximum in price
        if (
            len(self.data) >= 3
            and self.datahigh[-1] > self.datahigh[-2]
            and self.datahigh[-1] > self.datahigh[0]
        ):
            self.price_highs.append(self.datahigh[-1])
            self.macd_highs.append(self.macd_line[-1])

            # Keep only the last few values
            if len(self.price_highs) > self.params.divergence_window:
                self.price_highs.pop(0)
                self.macd_highs.pop(0)

        # Log current indicators periodically
        if len(self) % 20 == 0:
            self.log(
                f"Close: {self.dataclose[0]:.2f}, MACD: {self.macd_line[0]:.4f}, "
                f"Signal: {self.signal_line[0]:.4f}, RSI: {self.rsi[0]:.2f}"
            )

        # Check if we are in a position
        if not self.position:
            # ENTRY LOGIC

            # Check for bullish divergence and buy signal
            bullish_div = self.detect_bullish_divergence()

            # Only enter when MACD crosses above signal line (momentum confirmation)
            macd_signal = self.macd_cross_above > 0

            if bullish_div and macd_signal:
                self.log("BULLISH DIVERGENCE DETECTED - BUY SIGNAL")

                # Calculate stop loss price - tighter stop loss for divergence trades
                # Use recent low or a percentage-based stop, whichever is closer
                percent_stop = self.dataclose[0] * (1 - self.params.stop_loss_pct)
                swing_stop = (
                    min(self.datalow[0], self.datalow[-1], self.datalow[-2]) * 0.99
                )
                stop_price = max(
                    percent_stop, swing_stop
                )  # Use the higher (closer) stop price

                # Calculate position size based on risk
                size = self.calculate_position_size(stop_price)

                if size > 0:
                    self.log(f"BUY ORDER - Size: {size}, Stop: {stop_price:.2f}")
                    self.order = self.buy(size=size)

                    # Set stop loss and take profit orders
                    self.sell(exectype=bt.Order.Stop, price=stop_price, size=size)

                    # Set take profit at 2:1 reward-to-risk ratio
                    risk_amount = self.dataclose[0] - stop_price
                    take_profit_price = self.dataclose[0] + (risk_amount * 2)

                    self.sell(
                        exectype=bt.Order.Limit, price=take_profit_price, size=size
                    )

                    # Update last trade date for throttling
                    self.last_trade_date = self.datas[0].datetime.date(0)

            # Check for bearish divergence and sell signal
            bearish_div = self.detect_bearish_divergence()

            # Only enter when MACD crosses below signal line (momentum confirmation)
            macd_signal = self.macd_cross_below < 0

            if bearish_div and macd_signal:
                self.log("BEARISH DIVERGENCE DETECTED - SELL SIGNAL")

                # Calculate stop loss price - use recent high or percentage-based stop
                percent_stop = self.dataclose[0] * (1 + self.params.stop_loss_pct)
                swing_stop = (
                    max(self.datahigh[0], self.datahigh[-1], self.datahigh[-2]) * 1.01
                )
                stop_price = min(
                    percent_stop, swing_stop
                )  # Use the lower (closer) stop price

                # Calculate position size based on risk
                size = self.calculate_position_size(stop_price)

                if size > 0:
                    self.log(f"SELL ORDER - Size: {size}, Stop: {stop_price:.2f}")
                    self.order = self.sell(size=size)

                    # Set stop loss and take profit orders
                    self.buy(exectype=bt.Order.Stop, price=stop_price, size=size)

                    # Set take profit at 2:1 reward-to-risk ratio
                    risk_amount = stop_price - self.dataclose[0]
                    take_profit_price = self.dataclose[0] - (risk_amount * 2)

                    self.buy(
                        exectype=bt.Order.Limit, price=take_profit_price, size=size
                    )

                    # Update last trade date for throttling
                    self.last_trade_date = self.datas[0].datetime.date(0)
        else:
            # EXIT LOGIC - Already handled by stop loss and take profit orders
            # Additional exit logic could be added here if needed

            # Example: Exit if MACD crosses in opposite direction of the trade
            if self.position.size > 0 and self.macd_cross_below < 0:
                self.log("MACD REVERSED - EXIT LONG POSITION")
                self.order = self.close()
            elif self.position.size < 0 and self.macd_cross_above > 0:
                self.log("MACD REVERSED - EXIT SHORT POSITION")
                self.order = self.close()

    def notify_order(self, order):
        """Handle order status updates"""
        if order.status in [order.Submitted, order.Accepted]:
            # Order submitted/accepted - nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED - Price: {order.executed.price:.2f}, Size:"
                    f" {order.executed.size}, Value: {order.executed.value:.2f}, Comm:"
                    f" {order.executed.comm:.2f}"
                )
            else:
                self.log(
                    f"SELL EXECUTED - Price: {order.executed.price:.2f}, Size:"
                    f" {order.executed.size}, Value: {order.executed.value:.2f}, Comm:"
                    f" {order.executed.comm:.2f}"
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order Canceled/Margin/Rejected: {order.status}")

        # Reset the order
        self.order = None

    def notify_trade(self, trade):
        """Log trade information when a trade is closed"""
        if not trade.isclosed:
            return

        # Calculate trade metrics
        pnl = trade.pnl  # Gross profit and loss
        pnlcomm = trade.pnlcomm  # Net profit and loss (after commission)

        # Add to trade history for analysis
        self.trade_history.append({
            "entry_date": self.data.datetime.date(-trade.barlen),
            "exit_date": self.data.datetime.date(0),
            "pnl": pnlcomm,
            "bars_held": trade.barlen,
        })

        # Log trade details
        self.log(
            f"TRADE CLOSED - Gross Profit: {pnl:.2f}, Net Profit: {pnlcomm:.2f}, Bars"
            f" Held: {trade.barlen}"
        )


def run_backtest(
    ticker="SPY", start_date="2018-01-01", end_date="2023-01-01", plot=True
):
    """
    Run a backtest for the MACD Divergence Strategy.

    Args:
        ticker (str): The ticker symbol to backtest
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        plot (bool): Whether to plot the results

    Returns:
        The results of the backtest
    """
    # Create a backtest cerebro entity
    cerebro = bt.Cerebro()

    # Add strategy
    cerebro.addstrategy(MACDDivergenceStrategy)

    # Get data
    data = get_db_data(ticker, start_date, end_date)
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)

    # Set starting cash and add commission
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Add analyzers
    add_standard_analyzers(cerebro)

    # Run backtest
    initial_value = cerebro.broker.getvalue()
    print(f"Starting Portfolio Value: ${initial_value:.2f}")
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: ${final_value:.2f}")

    # Use the standardized performance metrics function
    print_performance_metrics(cerebro, results)

    # Plot if requested
    if plot:
        cerebro.plot(style="candlestick")

    return results


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MACD Divergence Strategy Backtest")
    parser.add_argument("-t", "--ticker", type=str, default="SPY", help="Ticker symbol")
    parser.add_argument(
        "-s", "--start", type=str, default="2018-01-01", help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "-e", "--end", type=str, default="2023-01-01", help="End date (YYYY-MM-DD)"
    )
    parser.add_argument("-p", "--plot", action="store_true", help="Plot results")
    parser.add_argument(
        "-c", "--cash", type=float, default=100000.0, help="Initial cash amount"
    )

    # Strategy parameters
    parser.add_argument("--fast-ema", type=int, default=12, help="Fast EMA period")
    parser.add_argument("--slow-ema", type=int, default=26, help="Slow EMA period")
    parser.add_argument(
        "--signal-period", type=int, default=9, help="Signal line period"
    )
    parser.add_argument("--rsi-period", type=int, default=14, help="RSI period")
    parser.add_argument(
        "--risk-pct", type=float, default=2.0, help="Risk percentage per trade"
    )
    parser.add_argument(
        "--stop-loss-pct", type=float, default=5.0, help="Stop loss percentage"
    )
    parser.add_argument(
        "--throttle-days", type=int, default=5, help="Trade throttle days"
    )

    args = parser.parse_args()

    print(
        f"Running MACD Divergence Strategy on {args.ticker} from {args.start} to"
        f" {args.end}"
    )
    print(f"Strategy Parameters:")
    print(f"  - Fast EMA: {args.fast_ema}")
    print(f"  - Slow EMA: {args.slow_ema}")
    print(f"  - Signal Period: {args.signal_period}")
    print(f"  - RSI Period: {args.rsi_period}")
    print(f"  - Risk Percentage: {args.risk_pct}%")
    print(f"  - Stop Loss: {args.stop_loss_pct}%")
    print(f"  - Trade Throttle: {args.throttle_days} days")
    print("\nStarting Backtest...\n")

    # Create a cerebro instance and run the backtest
    cerebro = bt.Cerebro()

    # Add strategy with parameters
    cerebro.addstrategy(
        MACDDivergenceStrategy,
        fast_ema=args.fast_ema,
        slow_ema=args.slow_ema,
        signal_period=args.signal_period,
        rsi_period=args.rsi_period,
        risk_pct=args.risk_pct,
        stop_loss_pct=args.stop_loss_pct,
        trade_throttle_days=args.throttle_days,
    )

    # Get data
    data = get_db_data(args.ticker, args.start, args.end)
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)

    # Set starting cash and commission
    cerebro.broker.setcash(args.cash)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Add analyzers using standard names expected by print_performance_metrics
    add_standard_analyzers(cerebro)

    # Run the backtest
    initial_value = cerebro.broker.getvalue()
    print(f"Starting Portfolio Value: ${initial_value:.2f}")
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: ${final_value:.2f}")

    # Use the standardized performance metrics function
    print_performance_metrics(cerebro, results)

    # Plot if requested
    if args.plot:
        cerebro.plot(style="candlestick")
