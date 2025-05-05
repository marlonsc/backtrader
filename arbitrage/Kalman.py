import pandas as pd
output_file = 'D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5'
df0 = pd.read_hdf(output_file, key='/J').reset_index()
df1 = pd.read_hdf(output_file, key='/JM').reset_index()
"""
the df0 and df1 consist of data from 焦煤(JM) and 焦炭(J) respectively
they share the same columns, including:
underlying_symbol: str, "JM" or "J"
datetime: str, YYYY-MM-DD
open: float, open price
close: float, close price
"""
import numpy as np
import backtrader as bt
import datetime
from pykalman import KalmanFilter
from statsmodels.regression.linear_model import OLS
from statsmodels.tsa.stattools import adfuller

# Function to calculate hedge ratio using Kalman Filter
def calculate_dynamic_hedge_ratio(y, x):
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
    spread_lag = spread.shift(1).dropna()
    spread = spread.iloc[1:]

    model = OLS(spread, spread_lag).fit()
    beta = model.params[0]

    half_life = -np.log(2) / beta if beta < 0 else 100
    return max(1, int(half_life))

# Check cointegration using ADF test
def check_cointegration(series_y, series_x):
    model = OLS(series_y, series_x).fit()
    hedge_ratio = model.params[0]
    spread = series_y - hedge_ratio * series_x

    adf_result = adfuller(spread)
    p_value = adf_result[1]

    return p_value < 0.05, hedge_ratio, p_value

# Custom data feed for spread
class SpreadData(bt.feeds.PandasData):
    lines = ('hedge_ratio', 'spread')
    params = (
        ('hedge_ratio', -1),
        ('spread', -1),
    )

# Kalman Pairs Trading Strategy
class KalmanPairTradingStrategy(bt.Strategy):
    params = (
        ('z_entry', 1),     # Z-score threshold for entry
        ('z_exit', 0.0),      # Z-score threshold for exit
        ('lookback', 15),     # Default lookback period (updated with half-life)
        ('size0', 10),         # Size for first asset
        ('size1', 14),         # Size for second asset (dynamically adjusted)
    )

    def __init__(self):
        self.data0 = self.datas[0]  # J futures
        self.data1 = self.datas[1]  # JM futures
        self.spread_data = self.datas[2]  # Spread data

        # Z-score calculation
        self.ma = bt.indicators.SimpleMovingAverage(self.spread_data.spread, period=self.p.lookback)
        self.std = bt.indicators.StandardDeviation(self.spread_data.spread, period=self.p.lookback)
        self.z_score = (self.spread_data.spread - self.ma) / self.std

        self.position_type = None

    def next(self):
        if len(self) < self.p.lookback:
            return

        z = self.z_score[0]
        hedge_ratio = self.spread_data.hedge_ratio[0]

        # Dynamic position sizing based on hedge ratio
        self.p.size1 = round(self.p.size0 * abs(hedge_ratio))

        pos0 = self.getposition(self.data0).size
        pos1 = self.getposition(self.data1).size

        # Entry logic
        if not pos0 and not pos1:  # No open positions
            if z < -self.p.z_entry:  # Spread is below mean (buy spread)
                self.position_type = 'long'
                self.buy(data=self.data0, size=self.p.size0)  # Buy J
                self.sell(data=self.data1, size=self.p.size1)  # Sell JM

            elif z > self.p.z_entry:  # Spread is above mean (sell spread)
                self.position_type = 'short'
                self.sell(data=self.data0, size=self.p.size0)  # Sell J
                self.buy(data=self.data1, size=self.p.size1)  # Buy JM

        # Exit logic
        elif self.position_type is not None:
            if (self.position_type == 'long' and z >= self.p.z_exit) or \
               (self.position_type == 'short' and z <= self.p.z_exit):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None

    def notify_trade(self, trade):
        if trade.isclosed:
            print(f'TRADE {trade.ref} CLOSED, PROFIT: GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')
        elif trade.justopened:
            print(f'TRADE {trade.ref} OPENED, SIZE {trade.size:2d}, PRICE {trade.price:.2f}')

# Main script execution
# Load data
output_file = 'D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5'
df0 = pd.read_hdf(output_file, key='/J').reset_index()
df1 = pd.read_hdf(output_file, key='/JM').reset_index()

# Prepare close prices for analysis
j_prices = df0['close']
jm_prices = df1['close']

# Check for cointegration
is_cointegrated, initial_hedge, p_value = check_cointegration(j_prices, jm_prices)
print(f"Cointegration test: {'Passed' if is_cointegrated else 'Failed'} (p-value: {p_value:.4f})")

# Calculate dynamic hedge ratio and spread using Kalman filter
hedge_ratio, intercept, spread = calculate_dynamic_hedge_ratio(j_prices, jm_prices)

# Calculate half-life for optimal parameter setting
half_life = calculate_half_life(pd.Series(spread))
print(f"Half-life of mean reversion: {half_life} days")

# Create spread dataframe
df_spread = df0.copy()
df_spread['hedge_ratio'] = hedge_ratio
df_spread['spread'] = spread

# Setup backtrader
fromdate = datetime.datetime(2023, 1, 1)
todate = datetime.datetime(2025, 1, 1)

# Create data feeds
data0 = bt.feeds.PandasData(dataname=df0, datetime='date', nocase=True, fromdate=fromdate, todate=todate)
data1 = bt.feeds.PandasData(dataname=df1, datetime='date', nocase=True, fromdate=fromdate, todate=todate)
data2 = SpreadData(dataname=df_spread, datetime='date', nocase=True,
                  fromdate=fromdate, todate=todate,
                  hedge_ratio='hedge_ratio', spread='spread')

# Create backtrader engine
cerebro = bt.Cerebro(stdstats=False)
cerebro.adddata(data0, name='J')
cerebro.adddata(data1, name='JM')
cerebro.adddata(data2, name='spread')

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
cerebro.addanalyzer(bt.analyzers.DrawDown)
cerebro.addanalyzer(bt.analyzers.ROIAnalyzer, period=bt.TimeFrame.Days)
cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                    timeframe=bt.TimeFrame.Days,
                    riskfreerate=0,
                    annualize=True)
cerebro.addanalyzer(bt.analyzers.Returns, tann=bt.TimeFrame.Days)
cerebro.addanalyzer(bt.analyzers.CAGRAnalyzer, period=bt.TimeFrame.Days)

# Add observers
cerebro.addobserver(bt.observers.CashValue)
cerebro.addobserver(bt.observers.BuySell)
cerebro.addobserver(bt.observers.CumValue)

# Run backtest
results = cerebro.run()

# Get analysis results
drawdown = results[0].analyzers.drawdown.get_analysis()
sharpe = results[0].analyzers.sharperatio.get_analysis()
roi = results[0].analyzers.roianalyzer.get_analysis()
total_returns = results[0].analyzers.returns.get_analysis()
cagr = results[0].analyzers.cagranalyzer.get_analysis()

# Print results
print("=============回测结果================")
print(f"\nSharpe Ratio: {sharpe['sharperatio']:.2f}")
print(f"Drawdown: {drawdown['max']['drawdown']:.2f} %")
print(f"Annualized/Normalized return: {total_returns['rnorm100']:.2f}%")
print(f"Total compound return: {roi['roi100']:.2f}%")
print(f"年化收益: {cagr['cagr']:.2f}")
print(f"夏普比率: {cagr['sharpe']:.2f}")

# Plot results
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = [12, 8]  # Set a larger figure size
plt.rcParams['image.cmap'] = 'viridis'     # Set a specific colormap
cerebro.plot(volume=False, spread=True, barup='green', bardown='red',
             style='candle', numfigs=1, iplot=False, fmt='svg')