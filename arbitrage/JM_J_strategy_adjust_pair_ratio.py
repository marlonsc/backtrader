# Copyright (c) 2025 backtrader contributors
"""Dynamic spread trading strategy for JM/J using Backtrader. This module demonstrates
how to set up a pair trading strategy with dynamic ratio adjustment and built-in
analyzers."""
"""

import datetime

import pandas as pd
import backtrader as bt
from backtrader.indicators.sma import MovingAverageSimple as SimpleMovingAverage
from backtrader.indicators.deviation import StandardDeviation
from backtrader.analyzers.drawdown import DrawDown
from backtrader.analyzers.sharpe import SharpeRatio
from backtrader.analyzers.returns import Returns
from backtrader.analyzers.tradeanalyzer import TradeAnalyzer

# https://mp.weixin.qq.com/s/na-5duJiRM1fTJF0WrcptA


def calculate_rolling_spread(df0, df1, window: int = 90):
"""Calculate rolling β and spread

Args::
    df0: 
    df1: 
    window: (Default value = 90)"""
    window: (Default value = 90)"""
    # 1. Align and merge prices
    df = (
        df0.set_index("date")["close"]
        .rename("close0")
        .to_frame()
        .join(df1.set_index("date")["close"].rename("close1"), how="inner")
    )

    # 2. Calculate rolling β (vectorized, much faster than rolling-apply)
    cov = df["close0"].rolling(window).cov(df["close1"])
    var1 = df["close1"].rolling(window).var()
    beta = (cov / var1).round(1)

    # 3. Calculate spread
    spread = df["close0"] - beta * df["close1"]

    # 4. Organize output
    out = (
        pd.DataFrame({"date": df.index, "beta": beta, "close": spread})
        .dropna()
        .reset_index(drop=True)
    )

    # 5. Ensure date column is of correct date type
    out["date"] = pd.to_datetime(out["date"])

    return out


# Read data
output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"
df0 = pd.read_hdf(output_file, key="/J").reset_index()
df1 = pd.read_hdf(output_file, key="/JM").reset_index()

# Ensure date column format is correct
df0["date"] = pd.to_datetime(df0["date"])
df1["date"] = pd.to_datetime(df1["date"])

# Calculate rolling spread
df_spread = calculate_rolling_spread(df0, df1, window=60)
print("Rolling spread calculation completed, example coefficients:")
print(df_spread.head())

fromdate = datetime.datetime(2018, 1, 1)
todate = datetime.datetime(2025, 1, 1)

# Create custom data class to support beta column


class SpreadData(bt.feeds.PandasData):
""""""
""""""
        """Initialize the strategy and indicators."""
        super().__init__()
        self.boll_mid = SimpleMovingAverage(self.data2.close, period=self.p.period)
        self.boll_std = StandardDeviation(self.data2.close, period=self.p.period)
        self.boll_top = self.boll_mid + self.p.devfactor * self.boll_std
        self.boll_bot = self.boll_mid - self.p.devfactor * self.boll_std
        self.order = None
        self.entry_price = 0

    def next(self):
""""""
"""Place order with dynamic ratio

Args::
    short:"""
    short:"""
        # Confirm trade size is valid
        if not hasattr(self, "size0") or not hasattr(self, "size1"):
            self.size0 = 10  # Default value
            self.size1 = (
                round(self.data2.beta[0] * 10)
                if not pd.isna(self.data2.beta[0])
                else 14
            )

        if short:
            print(f"Short J {self.size0} lots, Long JM {self.size1} lots")
            self.sell(data=self.data0, size=self.size0)
            self.buy(data=self.data1, size=self.size1)
        else:
            print(f"Long J {self.size0} lots, Short JM {self.size1} lots")
            self.buy(data=self.data0, size=self.size0)
            self.sell(data=self.data1, size=self.size1)
        self.entry_price = self.data2.close[0]

    def _close_positions(self):
""""""
"""Args::
    trade:"""
    trade:"""
        if trade.isclosed:
            print(
                "TRADE %s CLOSED, PROFIT: GROSS %.2f, NET %.2f, PRICE %d"
                % (
                    trade.ref,
                    pd.Timestamp(trade.dtclose),
                    trade.pnl,
                    trade.pnlcomm,
                    trade.value,
                )
            )
        elif trade.justopened:
            print(
                "TRADE %s OPENED %s  , SIZE %2d, PRICE %d "
                % (
                    trade.ref,
                    pd.Timestamp(trade.dtopen),
                    trade.size,
                    trade.value,
                )
            )

    # def notify_order(self, order):
    #     if order.status in [order.Submitted, order.Accepted]:
    #         # Order status submitted/accepted, in pending order status.
    #         return
    #
    #     # Order is decided, execute the following statements
    #     if order.status in [order.Completed]:
    #         if order.isbuy():
    #             print(f'executed date {bt.num2date(order.executed.dt)},executed price {order.executed.price}, created date {bt.num2date(order.created.dt)}')


# Create backtest engine
cerebro = bt.Cerebro()
cerebro.adddata(data0, name="data0")
cerebro.adddata(data1, name="data1")
cerebro.adddata(data2, name="spread")

# cerebro.broker.setcommission(
#     commission=0.001,  # 0.1% fee rate
#     margin=False,       # Non-margin trading
#     mult=1,            # Price multiplier
# )
# # # Percentage slippage
# cerebro.broker.set_slippage_perc(
#     perc=0.0005,        # 0.5% slippage
#     slip_open=True,    # Affects opening price
#     slip_limit=True,   # Affects limit orders
#     slip_match=True,   # Adjusts execution price
#     slip_out=True      # Allows slippage out of price range
# )

# Add strategy
cerebro.addstrategy(DynamicSpreadStrategy)
##########################################################################
# Set initial capital
cerebro.broker.setcash(100000)
cerebro.broker.set_shortcash(False)
cerebro.addanalyzer(DrawDown, _name="drawdown")
cerebro.addanalyzer(SharpeRatio, _name="sharperatio")
cerebro.addanalyzer(Returns, _name="returns")
cerebro.addanalyzer(TradeAnalyzer, _name="tradeanalyzer")

# cerebro.addobserver(bt.observers.CashValue)
cerebro.addanalyzer(
    SharpeRatio,
    timeframe=bt.TimeFrame.Days,  # Calculate based on daily data
    riskfreerate=0,  # Default annualized 1% risk-free rate
    annualize=True,  # Do not annualize
)
cerebro.addanalyzer(
    Returns,
    tann=bt.TimeFrame.Days,  # Annualization factor, 252 trading days
)
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

# cerebro.addobserver(bt.observers.CashValue)
# cerebro.addobserver(bt.observers.Value)

cerebro.addobserver(bt.observers.Trades)
# cerebro.addobserver(bt.observers.BuySell)
cerebro.addobserver(bt.observers.CumValue)

# Run backtest
results = cerebro.run()
#
# Get analysis results
drawdown = results[0].analyzers.drawdown.get_analysis()
sharpe = results[0].analyzers.sharperatio.get_analysis()
# Get total return rate
total_returns = results[0].analyzers.returns.get_analysis()
# trade_analysis = results[0].analyzers.tradeanalyzer.get_analysis()  #
# Get analysis results by name

# # Print analysis results
print("=============Backtest Results================")
print(f"\nSharpe Ratio: {sharpe['sharperatio']:.2f}")
print(f"Drawdown: {drawdown['max']['drawdown']:.2f} %")
print(f"Annualized/Normalized return: {total_returns['rnorm100']:.2f}%")  #
# Annualized return: {cagr['cagr']:.2f}
# Sharpe ratio: {cagr['sharpe']:.2f}
# Draw results
cerebro.plot(volume=False, spread=True)
