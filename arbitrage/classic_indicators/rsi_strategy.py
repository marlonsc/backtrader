# Copyright (c) 2025 backtrader contributors
"""RSI Arbitrage Strategy for Backtrader
Implements a pair trading strategy using a manually calculated RSI on the price
difference between two instruments."""
import datetime

import backtrader as bt
import pandas as pd


class RSIArbitrageStrategy(bt.Strategy):
    """
    Arbitrage strategy using a manually calculated RSI on the price difference between
    two assets.
    """
    params = (
        ("rsi_period", 14),  # RSI period
        ("rsi_overbought", 70),  # RSI overbought threshold
        ("rsi_oversold", 30),  # RSI oversold threshold
        ("printlog", False),
    )

    def __init__(self):
        """
        Initialize the RSIArbitrageStrategy. Computes the price difference, RSI, and sets
        up trading state variables.
        """
        self.price_diff = self.data0.close - 1.4 * self.data1.close
        self.price_diff_rsi = ManualRSI(self.price_diff, period=self.p.rsi_period)
        self.order = None
        self.position_type = None

    def next(self):
        """
        Main strategy logic for each bar. Handles entry and exit conditions based on RSI
        levels.
        """
        if self.order:
            return
        if self.position:
            # Exit conditions
            if (
                self.position_type == "long_j_short_jm"
                and self.price_diff_rsi[0] >= self.p.rsi_overbought
            ):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(
                        f"Exit: price diff={self.price_diff[0]:.2f}, "
                        f"RSI={self.price_diff_rsi[0]:.2f}"
                    )
            elif (
                self.position_type == "short_j_long_jm"
                and self.price_diff_rsi[0] <= self.p.rsi_oversold
            ):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(
                        f"Exit: price diff={self.price_diff[0]:.2f}, "
                        f"RSI={self.price_diff_rsi[0]:.2f}"
                    )
        else:
            # Entry conditions
            if self.price_diff_rsi[0] >= self.p.rsi_overbought:
                # Short J, long JM
                self.order = self.sell(data=self.data0, size=10)
                self.order = self.buy(data=self.data1, size=14)
                self.position_type = "short_j_long_jm"
                if self.p.printlog:
                    print(
                        f"Entry: short J, long JM, price diff={self.price_diff[0]:.2f}, "
                        f"RSI={self.price_diff_rsi[0]:.2f}"
                    )
            elif self.price_diff_rsi[0] <= self.p.rsi_oversold:
                # Long J, short JM
                self.order = self.buy(data=self.data0, size=10)
                self.order = self.sell(data=self.data1, size=14)
                self.position_type = "long_j_short_jm"
                if self.p.printlog:
                    print(
                        f"Entry: long J, short JM, price diff={self.price_diff[0]:.2f}, "
                        f"RSI={self.price_diff_rsi[0]:.2f}"
                    )

    def notify_order(self, order):
        """
        Handle order notifications and print execution details if logging is enabled.
        """
        if order.status in [order.Completed]:
            if self.p.printlog:
                if order.isbuy():
                    print(
                        f"Buy executed: price={order.executed.price:.2f}, "
                        f"cost={order.executed.value:.2f}, "
                        f"commission={order.executed.comm:.2f}"
                    )
                else:
                    print(
                        f"Sell executed: price={order.executed.price:.2f}, "
                        f"cost={order.executed.value:.2f}, "
                        f"commission={order.executed.comm:.2f}"
                    )
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print("Order canceled/rejected/margin")
        self.order = None

def load_data(symbol1, symbol2, fromdate, todate):
    """
    Load two symbols from HDF5 and return as Backtrader PandasData feeds.

    Args:
        symbol1 (str): Key for the first symbol in the HDF5 file.
        symbol2 (str): Key for the second symbol in the HDF5 file.
        fromdate (datetime): Start date for the data.
        todate (datetime): End date for the data.

    Returns:
        tuple: (data0, data1) as Backtrader PandasData feeds.
    """
    output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"
    try:
        df0 = pd.read_hdf(output_file, key=symbol1).reset_index()
        df1 = pd.read_hdf(output_file, key=symbol2).reset_index()
        date_col = [col for col in df0.columns if "date" in col.lower()]
        if not date_col:
            raise ValueError("No date column found in dataset")
        df0 = df0.set_index(pd.to_datetime(df0[date_col[0]]))
        df1 = df1.set_index(pd.to_datetime(df1[date_col[0]]))
        df0 = df0.sort_index().loc[fromdate:todate]
        df1 = df1.sort_index().loc[fromdate:todate]
        data0 = bt.feeds.PandasData(df0)
        data1 = bt.feeds.PandasData(df1)
        return data0, data1
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None

def run_strategy():
    """
    Run the RSI arbitrage backtest, print results, and plot the equity curve.
    """
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.set_slippage_perc(perc=0.0005)
    cerebro.broker.set_shortcash(False)
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)
    data0, data1 = load_data("/J", "/JM", fromdate, todate)
    if data0 is None or data1 is None:
        print("Failed to load data. Please check file path and data format.")
        return
    cerebro.adddata(data0, name="J")
    cerebro.adddata(data1, name="JM")
    cerebro.addstrategy(RSIArbitrageStrategy, printlog=True)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe_ratio")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    print("Initial cash: %.2f" % cerebro.broker.getvalue())
    results = cerebro.run()
    print("Final cash: %.2f" % cerebro.broker.getvalue())
    strat = results[0]
    print("Sharpe Ratio:", strat.analyzers.sharpe_ratio.get_analysis()["sharperatio"])
    print("Max Drawdown:", strat.analyzers.drawdown.get_analysis()["max"]["drawdown"])
    print("Annualized Return:", strat.analyzers.returns.get_analysis()["rnorm100"])
    # cerebro.plot()

if __name__ == "__main__":
    run_strategy()

# Implement manual RSI calculation if bt.indicators.RSI does not exist
class ManualRSI(bt.Indicator):
    """
    Manual implementation of the RSI indicator for use in the strategy if
    bt.indicators.RSI is not available.
    """
    lines = ("rsi",)
    params = (("period", 14),)

    def __init__(self):
        diff = self.data - self.data(-1)
        up = bt.If(diff > 0, diff, 0.0)
        down = bt.If(diff < 0, -diff, 0.0)
        self.lines.rsi = 100 - 100 / (
            1
            + bt.indicators.ExponentialMovingAverage(up, period=self.p.period)
            / bt.indicators.ExponentialMovingAverage(down, period=self.p.period)
        )
