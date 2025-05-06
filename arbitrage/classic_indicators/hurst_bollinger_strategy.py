# Copyright (c) 2025 backtrader contributors
"""
Hurst-Bollinger Arbitrage Strategy for Backtrader

Implements a pair trading strategy using the Hurst exponent and Bollinger Bands on the
price difference between two instruments. Includes parameter optimization and heatmap
visualization.
"""
import datetime
import itertools
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import backtrader as bt
from backtrader.indicators.bollinger import BollingerBands
from backtrader.indicators.hurst import HurstExponent as Hurst
from backtrader.analyzers.drawdown import DrawDown
from backtrader.analyzers.sharpe import SharpeRatio
from backtrader.analyzers.returns import Returns

class HurstBollingerStrategy(bt.Strategy):
    """
    Pair trading strategy using the Hurst exponent and Bollinger Bands on the price
    difference between two assets.
    """
    params = (
        ("hurst_period", 20),  # Hurst exponent calculation period
        ("bollinger_period", 7),  # Bollinger Band period
        ("bollinger_dev", 1.5),  # Bollinger Band standard deviation multiplier
        ("printlog", False),
    )

    def __init__(self):
        """
        Initialize the HurstBollingerStrategy. Computes the price difference, Hurst
        exponent, Bollinger Bands, and sets up trading state variables.
        """
        self.price_diff = self.data0.close - 1.4 * self.data1.close
        self.bollinger = BollingerBands(
            self.price_diff,
            period=self.p.bollinger_period,
            devfactor=self.p.bollinger_dev,
        )
        self.hurst = Hurst(self.price_diff, period=self.p.hurst_period)
        self.order = None
        self.position_type = None

    def next(self):
        """
        Main strategy logic for each bar. Handles entry and exit conditions based on the
        Hurst exponent and Bollinger Bands.
        """
        if self.order:
            return
        if self.position:
            # Exit conditions
            if (
                self.position_type == "long_j_short_jm"
                and self.price_diff[0] >= self.bollinger.mid[0]
            ):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(
                        f"Exit: price diff={self.price_diff[0]:.2f}, "
                        f"Hurst={self.hurst[0]:.2f}"
                    )
            elif (
                self.position_type == "short_j_long_jm"
                and self.price_diff[0] <= self.bollinger.mid[0]
            ):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(
                        f"Exit: price diff={self.price_diff[0]:.2f}, "
                        f"Hurst={self.hurst[0]:.2f}"
                    )
        else:
            # Entry conditions: Hurst > 0.5 (mean reversion) and price diff breaks band
            if self.hurst[0] > 0.5 and self.price_diff[0] >= self.bollinger.top[0]:
                # Short J, long JM
                self.order = self.buy(data=self.data0, size=10)
                self.order = self.sell(data=self.data1, size=14)
                self.position_type = "short_j_long_jm"
                if self.p.printlog:
                    print(
                        f"Entry: short J, long JM, price diff={self.price_diff[0]:.2f}, "
                        f"Hurst={self.hurst[0]:.2f}"
                    )
            elif self.hurst[0] > 0.5 and self.price_diff[0] <= self.bollinger.bot[0]:
                # Long J, short JM
                self.order = self.sell(data=self.data0, size=10)
                self.order = self.buy(data=self.data1, size=14)
                self.position_type = "long_j_short_jm"
                if self.p.printlog:
                    print(
                        f"Entry: long J, short JM, price diff={self.price_diff[0]:.2f}, "
                        f"Hurst={self.hurst[0]:.2f}"
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
        data0 = bt.feeds.PandasData(dataname=df0)
        data1 = bt.feeds.PandasData(dataname=df1)
        return data0, data1
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None

def optimize_parameters():
    """
    Optimize strategy parameters by running a grid search and print the best results.
    """
    hurst_periods = [10, 15, 20, 25, 30]
    bollinger_periods = [5, 7, 10, 14, 20]
    bollinger_devs = [1.0, 1.5, 2.0, 2.5, 3.0]
    results = []
    best_sharpe = -float("inf")
    best_params = None
    for hurst, period, dev in itertools.product(
        hurst_periods, bollinger_periods, bollinger_devs
    ):
        print(
            f"Parameter set: Hurst={hurst}, Bollinger period={period}, "
            f"StdDev Multiplier={dev}"
        )
        result = run_strategy(
            hurst_period=hurst, bollinger_period=period, bollinger_dev=dev
        )
        if result is None:
            print("Backtest failed")
            continue
        sharpe = result["sharpe"]
        drawdown = result["drawdown"]
        returns = result["returns"]
        sharpe_str = f"{sharpe:.4f}" if sharpe is not None else "N/A"
        drawdown_str = f"{drawdown:.2f}%" if drawdown is not None else "N/A"
        returns_str = f"{returns:.2f}%" if returns is not None else "N/A"
        print(
            f"Sharpe Ratio: {sharpe_str}, Max Drawdown: {drawdown_str}, "
            f"Annualized Return: {returns_str}"
        )
        print("-" * 50)
        if sharpe is not None:
            results.append(
                {
                    "hurst": hurst,
                    "period": period,
                    "dev": dev,
                    "sharpe": sharpe,
                    "drawdown": drawdown,
                    "returns": returns,
                }
            )
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_params = (hurst, period, dev)
    if best_params:
        print("\nBest parameter set:")
        print(f"Hurst period: {best_params[0]}")
        print(f"Bollinger period: {best_params[1]}")
        print(f"StdDev Multiplier: {best_params[2]}")
        print(f"Sharpe Ratio: {best_sharpe:.4f}")
    plot_heatmap(results)

def plot_heatmap(results):
    """
    Plot a heatmap of Sharpe ratios for each parameter combination.

    Args:
        results (list): List of dictionaries with parameter results.
    """
    if not results:
        print("No valid backtest results. Cannot plot heatmap.")
        return
    results_df = pd.DataFrame(results)
    unique_devs = sorted(results_df["dev"].unique())
    fig, axes = plt.subplots(1, len(unique_devs), figsize=(20, 5))
    if len(unique_devs) == 1:
        axes = [axes]
    for i, dev in enumerate(unique_devs):
        dev_data = results_df[results_df["dev"] == dev]
        heatmap_data = dev_data.pivot_table(
            index="hurst", columns="period", values="sharpe"
        )
        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt=".2f",
            cmap="RdYlGn",
            center=0,
            ax=axes[i],
        )
        axes[i].set_title(f"StdDev Multiplier = {dev}")
        axes[i].set_xlabel("Bollinger Period")
        axes[i].set_ylabel("Hurst Period")
    plt.tight_layout()
    plt.savefig("hurst_bollinger_heatmap.png")
    plt.close()
    print("Heatmap saved as hurst_bollinger_heatmap.png")

def run_strategy(hurst_period, bollinger_period, bollinger_dev, plot=False):
    """
    Run the Hurst-Bollinger arbitrage backtest, print results, and plot the equity curve.

    Args:
        hurst_period (int): Hurst exponent calculation period.
        bollinger_period (int): Bollinger Band period.
        bollinger_dev (float): Bollinger Band standard deviation multiplier.
        plot (bool): Whether to plot the results. Default is False.

    Returns:
        dict: Dictionary with Sharpe ratio, max drawdown, and annualized return.
    """
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(150000)
    cerebro.broker.set_slippage_perc(perc=0.0005)
    cerebro.broker.set_shortcash(False)
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)
    data0, data1 = load_data("/J", "/JM", fromdate, todate)
    if data0 is None or data1 is None:
        print("Failed to load data. Please check file path and data format.")
        return None
    cerebro.adddata(data0, name="J")
    cerebro.adddata(data1, name="JM")
    cerebro.addstrategy(
        HurstBollingerStrategy,
        hurst_period=hurst_period,
        bollinger_period=bollinger_period,
        bollinger_dev=bollinger_dev,
        printlog=False,
    )
    try:
        cerebro.addanalyzer(
            SharpeRatio,
            timeframe=bt.TimeFrame.Days,
            riskfreerate=0,
            annualize=True,
            _name="sharpe_ratio",
        )
        cerebro.addanalyzer(DrawDown, _name="drawdown")
        cerebro.addanalyzer(Returns, _name="returns")
    except AttributeError:
        print("cerebro.run() is not available in this Backtrader version.")
        results = []
    try:
        results = cerebro.run()
    except AttributeError:
        print("cerebro.run() is not available in this Backtrader version.")
        results = []
    result_dict = {"sharpe": None, "drawdown": None, "returns": None}
    if results and len(results) > 0:
        result = results[0]
        result_dict["sharpe"] = result.analyzers.sharpe_ratio.get_analysis().get(
            "sharperatio", None
        )
        result_dict["drawdown"] = (
            result.analyzers.drawdown.get_analysis()
            .get("max", {})
            .get("drawdown", None)
        )
        result_dict["returns"] = result.analyzers.returns.get_analysis().get(
            "rnorm100", None
        )
    if plot:
        cerebro.plot()
    return result_dict

if __name__ == "__main__":
    optimize_parameters()
    # run_strategy()
