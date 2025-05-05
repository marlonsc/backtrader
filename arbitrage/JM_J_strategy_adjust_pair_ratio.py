import datetime

import backtrader as bt
import pandas as pd

# https://mp.weixin.qq.com/s/na-5duJiRM1fTJF0WrcptA


def calculate_rolling_spread(df0, df1, window: int = 90):
    """Calculate rolling β and spread"""
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
    lines = ("beta",)  # Add beta line

    params = (
        ("datetime", "date"),  # Date column
        ("close", "close"),  # Spread column as close
        ("beta", "beta"),  # Beta column
        ("nocase", True),  # Column names are case-insensitive
    )


# Filter dataframes by date before passing to Backtrader
df0_bt = df0[(df0["date"] >= fromdate) & (df0["date"] <= todate)]
df1_bt = df1[(df1["date"] >= fromdate) & (df1["date"] <= todate)]
df_spread_bt = df_spread[
    (df_spread["date"] >= fromdate) & (df_spread["date"] <= todate)
]
data0 = bt.feeds.PandasData(dataname=df0_bt, datetime="date")
data1 = bt.feeds.PandasData(dataname=df1_bt, datetime="date")
data2 = SpreadData(dataname=df_spread_bt, datetime="date")


class DynamicSpreadStrategy(bt.Strategy):
    params = (
        ("period", 30),
        ("devfactor", 2),
    )

    def __init__(self):
        # Bollinger Bands indicator - using passed spread data
        self.boll = bt.indicators.BollingerBands(
            self.data2.close,
            period=self.p.period,
            devfactor=self.p.devfactor,
            subplot=False,
        )

        # Trading status
        self.order = None
        self.entry_price = 0

    def next(self):
        if self.order:
            return

        # Get current beta value
        current_beta = self.data2.beta[0]

        # Handle missing beta cases
        if pd.isna(current_beta) or current_beta <= 0:
            return

        # Dynamically set trade size
        self.size0 = 10  # Fixed J size
        self.size1 = round(current_beta * 10)  # Adjust JM size based on beta

        # Print debug information
        if len(self) % 20 == 0:  # Print every 20 bars to reduce output
            print(
                f"{self.datetime.date()}: beta={current_beta}, J:{self.size0} lots,"
                f" JM:{self.size1} lots"
            )

        # Use passed spread data
        spread = self.data2.close[0]
        mid = self.boll.lines.mid[0]
        pos = self.getposition(self.data0).size

        # Open/close position logic
        if pos == 0:
            if spread > self.boll.lines.top[0]:
                self._open_position(short=True)
            elif spread < self.boll.lines.bot[0]:
                self._open_position(short=False)
        else:
            if (spread <= mid and pos < 0) or (spread >= mid and pos > 0):
                self._close_positions()

    def _open_position(self, short):
        """Place order with dynamic ratio"""
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
        self.close(data=self.data0)
        self.close(data=self.data1)

    def notify_trade(self, trade):
        if trade.isclosed:
            print(
                "TRADE %s CLOSED %s, PROFIT: GROSS %.2f, NET %.2f, PRICE %d"
                % (
                    trade.ref,
                    bt.num2date(trade.dtclose),
                    trade.pnl,
                    trade.pnlcomm,
                    trade.value,
                )
            )
        elif trade.justopened:
            print(
                "TRADE %s OPENED %s  , SIZE %2d, PRICE %d "
                % (trade.ref, bt.num2date(trade.dtopen), trade.size, trade.value)
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
##########################################################################################
# Set initial capital
cerebro.broker.setcash(100000)
cerebro.broker.set_shortcash(False)
cerebro.addanalyzer(bt.analyzers.DrawDown)  # Drawdown analyzer
# ROIAnalyzer and CAGRAnalyzer are not standard Backtrader analyzers; removed for compatibility
cerebro.addanalyzer(
    bt.analyzers.SharpeRatio,
    timeframe=bt.TimeFrame.Days,  # Calculate based on daily data
    riskfreerate=0,  # Default annualized 1% risk-free rate
    annualize=True,  # Do not annualize
)
cerebro.addanalyzer(
    bt.analyzers.Returns,
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
total_returns = results[0].analyzers.returns.get_analysis()  # Get total return rate
# trade_analysis = results[0].analyzers.tradeanalyzer.get_analysis()  # Get analysis results by name

# # Print analysis results
print("=============Backtest Results================")
print(f"\nSharpe Ratio: {sharpe['sharperatio']:.2f}")
print(f"Drawdown: {drawdown['max']['drawdown']:.2f} %")
print(f"Annualized/Normalized return: {total_returns['rnorm100']:.2f}%")  #
# Annualized return: {cagr['cagr']:.2f}
# Sharpe ratio: {cagr['sharpe']:.2f}
# Draw results
cerebro.plot(volume=False, spread=True)
