# Copyright (c) 2025 backtrader contributors
"""Kalman filter-based pairs trading strategy for J/JM futures. Includes dynamic hedge
ratio calculation, cointegration check, and backtest with analyzers."""
"""
import datetime

import backtrader as bt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tsa.stattools import adfuller
from backtrader.indicators.deviation import StandardDeviation
from backtrader.analyzers.drawdown import DrawDown
from backtrader.analyzers.sharpe import SharpeRatio
from backtrader.analyzers.returns import Returns
from backtrader.analyzers.tradeanalyzer import TradeAnalyzer

# Remove or fix import errors for unavailable modules
try:
    from pykalman import KalmanFilter
except ImportError:
"""KalmanFilter class.

Description of the class functionality."""
"""__init__ function.

Returns:
    Description of return value
"""
            raise NotImplementedError("pykalman is not installed.")
"""filter function.

Returns:
    Description of return value
"""
            raise NotImplementedError("pykalman is not installed.")

output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"
df0 = pd.read_hdf(output_file, key="/J").reset_index()
df1 = pd.read_hdf(output_file, key="/JM").reset_index()
"""
the df0 and df1 consist of data from 焦煤(JM) and 焦炭(J) respectively
they share the same columns, including:
underlying_symbol: str, "JM" or "J"
datetime: str, YYYY-MM-DD
open: float, open price
close: float, close price
"""


# Function to calculate hedge ratio using Kalman Filter
def calculate_dynamic_hedge_ratio(y, x):
"""Args::
    y: 
    x:"""
    x:"""
    delta = 1e-5
    trans_cov = delta / (1 - delta) * np.eye(2)

    kf = KalmanFilter(
        n_dim_obs=1,
        n_dim_state=2,
        initial_state_mean=np.zeros(2),
        initial_state_covariance=np.ones((2, 2)),
        transition_matrices=np.eye(2),
        observation_matrices=np.vstack([np.ones(len(x)), x]).T.reshape(-1, 1, 2),
        transition_covariance=trans_cov,
    )

    state_means, _ = kf.filter(y.values)

    intercept = state_means[:, 0]
    hedge_ratio = state_means[:, 1]
    spread = y - (hedge_ratio * x + intercept)

    return hedge_ratio, intercept, spread


# Calculate half-life of mean reversion
def calculate_half_life(spread):
"""Args::
    spread:"""
"""Args::
    series_y: 
    series_x:"""
    series_x:"""
    model = OLS(series_y, series_x).fit()
    hedge_ratio = model.params[0]
    spread = series_y - hedge_ratio * series_x

    adf_result = adfuller(spread)
    p_value = adf_result[1]

    return p_value < 0.05, hedge_ratio, p_value


# Custom data feed for spread
class SpreadData(bt.feeds.PandasData):
""""""
""""""
""""""
""""""
"""Args::
    trade:"""
    trade:"""
        if trade.isclosed:
            print(
                f"TRADE {trade.ref} CLOSED, PROFIT: GROSS {trade.pnl:.2f}, NET"
                f" {trade.pnlcomm:.2f}"
            )
        elif trade.justopened:
            print(
                f"TRADE {trade.ref} OPENED, SIZE {trade.size:2d}, PRICE"
                f" {trade.price:.2f}"
            )


# Main script execution
# Load data
output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"
df0 = pd.read_hdf(output_file, key="/J").reset_index()
df1 = pd.read_hdf(output_file, key="/JM").reset_index()

# Prepare close prices for analysis
j_prices = df0["close"]
jm_prices = df1["close"]

# Check for cointegration
is_cointegrated, initial_hedge, p_value = check_cointegration(j_prices, jm_prices)
print(
    f"Cointegration test: {'Passed' if is_cointegrated else 'Failed'} (p-value:"
    f" {p_value:.4f})"
)

# Calculate dynamic hedge ratio and spread using Kalman filter
hedge_ratio, intercept, spread = calculate_dynamic_hedge_ratio(j_prices, jm_prices)

# Calculate half-life for optimal parameter setting
half_life = calculate_half_life(pd.Series(spread))
print(f"Half-life of mean reversion: {half_life} days")

# Create spread dataframe
df_spread = df0.copy()
df_spread["hedge_ratio"] = hedge_ratio
df_spread["spread"] = spread

# Setup backtrader
fromdate = datetime.datetime(2023, 1, 1)
todate = datetime.datetime(2025, 1, 1)

# Create data feeds
data0 = bt.feeds.PandasData(dataname=df0)
data1 = bt.feeds.PandasData(dataname=df1)
data2 = SpreadData(dataname=df_spread)

# Create backtrader engine
cerebro = bt.Cerebro()
cerebro.adddata(data0, name="J")
cerebro.adddata(data1, name="JM")
cerebro.adddata(data2, name="spread")

# # Set slippage
# cerebro.broker.set_slippage_perc(
#     perc=0.0005,
#     slip_open=True,
#     slip_limit=True,
#     slip_match=True,
#     slip_out=True
# )

# Add strategy with optimal lookback period
cerebro.addstrategy(KalmanPairTradingStrategy, lookback=half_life)

# Set initial cash
cerebro.broker.setcash(50000)
cerebro.broker.set_shortcash(False)

# Add analyzers
cerebro.addanalyzer(DrawDown, _name="drawdown")
cerebro.addanalyzer(SharpeRatio, _name="sharperatio")
cerebro.addanalyzer(Returns, _name="returns")
cerebro.addanalyzer(TradeAnalyzer, _name="tradeanalyzer")

# Run backtest
try:
    results = cerebro.run()
except AttributeError:
    print("cerebro.run() is not available in this Backtrader version.")
    results = []

# Get analysis results
drawdown = results[0].analyzers.drawdown.get_analysis()
sharpe = results[0].analyzers.sharperatio.get_analysis()
total_returns = results[0].analyzers.returns.get_analysis()
trade = results[0].analyzers.tradeanalyzer.get_analysis()

# Print results
print("=============回测结果================")
print(f"\nSharpe Ratio: {sharpe['sharperatio']:.2f}")
print(f"Drawdown: {drawdown['max']['drawdown']:.2f} %")
print(f"Annualized/Normalized return: {total_returns['rnorm100']:.2f}%")
print(f"Total compound return: {trade['roi100']:.2f}%")

# Plot results

plt.rcParams["figure.figsize"] = [12, 8]  # Set a larger figure size
plt.rcParams["image.cmap"] = "viridis"  # Set a specific colormap
cerebro.plot(
    volume=False,
    spread=True,
    barup="green",
    bardown="red",
    style="candle",
    numfigs=1,
    iplot=False,
    fmt="svg",
)
