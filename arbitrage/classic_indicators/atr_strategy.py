# Copyright (c) 2025 backtrader contributors
"""ATR Arbitrage Strategy for Backtrader
Implements a pair trading strategy using ATR and SMA bands on the price difference
between two instruments."""

import datetime

import backtrader as bt
import pandas as pd
from backtrader.analyzers.drawdown import DrawDown
from backtrader.analyzers.returns import Returns
from backtrader.analyzers.sharpe import SharpeRatio
from backtrader.feeds import PandasData
from backtrader.indicators.atr import AverageTrueRange as ATR
from backtrader.indicators.sma import MovingAverageSimple as SMA


class ATRArbitrageStrategy(bt.Strategy):
"""Arbitrage strategy using ATR and SMA bands on the price difference between two assets."""
    """

    params = (
        ("atr_period", 14),  # ATR period
        ("atr_multiplier", 2.0),  # ATR multiplier
        ("printlog", False),
    )

    def __init__(self):
"""Initialize the ATRArbitrageStrategy. Computes the price difference, ATR, SMA bands,
        and sets up trading state variables."""
        """
        super().__init__()
        # Compute price difference
        self.price_diff = self.data0.close - 1.4 * self.data1.close
        # Compute ATR of price difference
        self.price_diff_atr = ATR(data=self.data0, period=self.p.atr_period)
        # Compute SMA of price difference
        self.price_diff_ma = SMA(data=self.price_diff, period=self.p.atr_period)
        # Compute upper and lower bands
        self.upper_band = (
            self.price_diff_ma + self.p.atr_multiplier * self.price_diff_atr
        )
        self.lower_band = (
            self.price_diff_ma - self.p.atr_multiplier * self.price_diff_atr
        )
        # Trading state variables
        self.order = None
        self.position_type = None

    def next(self):
"""Main strategy logic for each bar. Handles entry and exit conditions based on ATR
        and SMA bands."""
        """
        if self.order:
            return
        # Trading logic
        if self.position:
            # Exit conditions
            if (
                self.position_type == "long_j_short_jm"
                and self.price_diff[0] >= self.price_diff_ma[0]
            ):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(
                        f"Exit: price diff={self.price_diff[0]:.2f}, ATR={self.price_diff_atr[0]:.2f}"
                    )
            elif (
                self.position_type == "short_j_long_jm"
                and self.price_diff[0] <= self.price_diff_ma[0]
            ):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(
                        f"Exit: price diff={self.price_diff[0]:.2f}, ATR={self.price_diff_atr[0]:.2f}"
                    )
        else:
            # Entry conditions
            if self.price_diff[0] >= self.upper_band[0]:
                # Short J, long JM
                self.order = self.sell(data=self.data0, size=10)
                self.order = self.buy(data=self.data1, size=14)
                self.position_type = "short_j_long_jm"
                if self.p.printlog:
                    print(
                        f"Entry: short J, long JM, price diff={self.price_diff[0]:.2f}, ATR={self.price_diff_atr[0]:.2f}"
                    )
            elif self.price_diff[0] <= self.lower_band[0]:
                # Long J, short JM
                self.order = self.buy(data=self.data0, size=10)
                self.order = self.sell(data=self.data1, size=14)
                self.position_type = "long_j_short_jm"
                if self.p.printlog:
                    print(
                        f"Entry: long J, short JM, price diff={self.price_diff[0]:.2f}, ATR={self.price_diff_atr[0]:.2f}"
                    )

    def notify_order(self, order):
"""Handle order notifications and print execution details if logging is enabled."""
        """
        if order.status in [order.Completed]:
            if self.p.printlog:
                if order.isbuy():
                    print(
                        f"Buy executed: price={order.executed.price:.2f}, cost={order.executed.value:.2f}, commission={order.executed.comm:.2f}"
                    )
                else:
                    print(
                        f"Sell executed: price={order.executed.price:.2f}, cost={order.executed.value:.2f}, commission={order.executed.comm:.2f}"
                    )
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print("Order canceled/rejected/margin")
        self.order = None


def load_data(symbol1, symbol2, fromdate, todate):
"""Load two symbols from HDF5 and return as Backtrader PandasData feeds.

Args::
        symbol1 (str): Key for the first symbol in the HDF5 file.
        symbol2 (str): Key for the second symbol in the HDF5 file.
        fromdate (datetime): Start date for the data.
        todate (datetime): End date for the data.

Returns::
        tuple: (data0, data1) as Backtrader PandasData feeds."""
    """
    output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"
    df0 = pd.read_hdf(output_file, key=symbol1).reset_index()
    df1 = pd.read_hdf(output_file, key=symbol2).reset_index()
    date_col = [col for col in df0.columns if "date" in col.lower()]
    if not date_col:
        raise ValueError("No date column found in dataset")
    df0 = df0.set_index(pd.to_datetime(df0[date_col[0]]))
    df1 = df1.set_index(pd.to_datetime(df1[date_col[0]]))
    df0 = df0.sort_index().loc[fromdate:todate]
    df1 = df1.sort_index().loc[fromdate:todate]
    data0 = PandasData(dataname=df0)
    data1 = PandasData(dataname=df1)
    return data0, data1


def run_strategy():
"""Run the ATR arbitrage backtest, print results, and plot the equity curve."""
    """
    # Create backtest engine
    cerebro = bt.Cerebro()
    # Set initial cash
    cerebro.broker.setcash(150000)
    # Set slippage
    cerebro.broker.set_slippage_perc(perc=0.0005)
    # Set commission
    cerebro.broker.setcommission(commission=0.0003)
    cerebro.broker.set_shortcash(False)
    # Load data
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)
    data0, data1 = load_data("/J", "/JM", fromdate, todate)
    if data0 is None or data1 is None:
        print("Failed to load data. Please check file path and data format.")
        return
    # Add data
    cerebro.adddata(data0, name="J")
    cerebro.adddata(data1, name="JM")
    # Add strategy
    cerebro.addstrategy(ATRArbitrageStrategy, printlog=True)
    # Add analyzers
    cerebro.addanalyzer(SharpeRatio, _name="sharpe_ratio")
    cerebro.addanalyzer(DrawDown, _name="drawdown")
    cerebro.addanalyzer(Returns, _name="returns")
    # Run backtest
    print("Initial cash: %.2f" % cerebro.broker.getvalue())
    results = cerebro.run()
    print("Final cash: %.2f" % cerebro.broker.getvalue())
    # Print analysis results
    strat = results[0]
    sharpe = strat.analyzers.sharpe_ratio.get_analysis().get("sharperatio", 0)
    drawdown = strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0)
    returns = strat.analyzers.returns.get_analysis().get("rnorm100", 0)
    print("Sharpe Ratio:", sharpe)
    print("Max Drawdown:", drawdown)
    print("Annualized Return:", returns)
    # Plot results
    cerebro.plot()


if __name__ == "__main__":
    run_strategy()
