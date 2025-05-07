import datetime

import backtrader as bt
import numpy as np
import pandas as pd


def calculate_rolling_spread(
    df0: pd.DataFrame,  # Must contain 'date' and price columns
    df1: pd.DataFrame,
    window: int = 30,
    fields=("open", "high", "low", "close"),
) -> pd.DataFrame:
    """Calculate rolling β, and generate spread for specified price fields:
spread_x = price0_x - β_{t-1} * price1_x"""
    # 1) Align and merge using closing prices (β still estimated using close)
    df = (
        df0.set_index("date")[["close"]]
        .rename(columns={"close": "close0"})
        .join(
            df1.set_index("date")[["close"]].rename(columns={"close": "close1"}),
            how="inner",
        )
    )

    # 2) Estimate β_t, then shift forward one day
    beta_raw = (
        df["close0"].rolling(window).cov(df["close1"])
        / df["close1"].rolling(window).var()
    )
    beta_shift = beta_raw.shift(1).round(1)  # Prevent future data + keep 1 decimal place

    # 3) Join β back to the main table (for easier vectorized calculation later)
    df = df.assign(beta=beta_shift)

    # 4) Calculate spread for each field
    out_cols = {"date": df.index, "beta": beta_shift}
    for f in fields:
        if f not in ("open", "high", "low", "close"):
            raise ValueError(f"Unknown field {f}")
        p0 = df0.set_index("date")[f]
        p1 = df1.set_index("date")[f]
        aligned = p0.to_frame(name=f"price0_{f}").join(
            p1.to_frame(name=f"price1_{f}"), how="inner"
        )
        spread_f = aligned[f"price0_{f}"] - beta_shift * aligned[f"price1_{f}"]
        out_cols[f"{f}"] = spread_f

    # 5) Organize output
    out = pd.DataFrame(out_cols).dropna().reset_index(drop=True)
    out["date"] = pd.to_datetime(out["date"])
    return out


# Create quantile indicator (custom)
class QuantileIndicator(bt.Indicator):
    lines = ("upper", "lower", "mid")
    params = (
        ("period", 30),
        ("upper_quantile", 0.9),  # Upper band quantile
        ("lower_quantile", 0.1),  # Lower band quantile
    )

    def __init__(self):
        self.addminperiod(self.p.period)
        self.spread_data = []

    def next(self):
        self.spread_data.append(self.data[0])
        if len(self.spread_data) > self.p.period:
            self.spread_data.pop(0)  # Maintain fixed length

        if len(self.spread_data) >= self.p.period:
            spread_array = np.array(self.spread_data)
            self.lines.upper[0] = np.quantile(spread_array, self.p.upper_quantile)
            self.lines.lower[0] = np.quantile(spread_array, self.p.lower_quantile)
            self.lines.mid[0] = np.median(spread_array)
        else:
            self.lines.upper[0] = self.data[0]
            self.lines.lower[0] = self.data[0]
            self.lines.mid[0] = self.data[0]


class DynamicSpreadQuantileStrategy(bt.Strategy):
    params = (
        ("lookback_period", 60),  # Lookback period
        ("upper_quantile", 0.9),  # Upper band quantile
        ("lower_quantile", 0.1),  # Lower band quantile
        ("max_positions", 3),  # Maximum number of position layers
        ("add_position_threshold", 0.1),  # Position adding threshold (percentage relative to the band)
        ("verbose", True),  # Whether to print detailed information
    )

    def __init__(self):
        # Calculate quantile indicators for the spread
        self.quantile = QuantileIndicator(
            self.data2.close,
            period=self.p.lookback_period,
            upper_quantile=self.p.upper_quantile,
            lower_quantile=self.p.lower_quantile,
        )
        # Trading status
        self.order = None
        self.entry_price = 0
        self.entry_direction = None  # Position direction: 'long'/'short'
        self.position_layers = 0  # Current position layers

        # Initialize order tracking
        self.order = None
        self.entry_price = 0

    def next(self):
        if self.order:
            return

        # Get current beta value
        current_beta = self.data2.beta[0]

        # Handle missing beta case
        if pd.isna(current_beta) or current_beta <= 0:
            return

        # Dynamically set trading size
        self.size0 = 10  # Fixed size for J
        self.size1 = round(current_beta * 10)  # Adjust JM size based on beta

        # Print debug information
        if self.p.verbose and len(self) % 20 == 0:  # Print every 20 bars to reduce output
            print(
                f"{self.datetime.date()}: beta={current_beta}, J:{self.size0} lots,"
                f" JM:{self.size1} lots"
            )

        # Use quantile indicators for trading decisions
        spread = self.data2.close[0]
        upper_band = self.quantile.upper[0]
        lower_band = self.quantile.lower[0]
        mid_band = self.quantile.mid[0]
        pos = self.getposition(self.data0).size

        # Open/close position logic
        if pos == 0:  # No position
            if spread > upper_band:
                # Spread above upper band, short the spread (long J, short JM)
                self._open_position(short=True)
            elif spread < lower_band:
                # Spread below lower band, long the spread (short J, long JM)
                self._open_position(short=False)
        else:  # Already have position
            # Automatic position adding logic
            if self.position_layers < self.p.max_positions:
                # Long position adding condition
                if pos > 0:
                    # Using lower_band as reference, add position as spread gets lower
                    next_layer = self.position_layers + 1
                    add_threshold = (
                        lower_band
                        - next_layer
                        * self.p.add_position_threshold
                        * (upper_band - lower_band)
                    )
                    if spread < add_threshold:
                        self._add_position(short=False)
                # Short position adding condition
                elif pos < 0:
                    # Using upper_band as reference, add position as spread gets higher
                    next_layer = self.position_layers + 1
                    add_threshold = (
                        upper_band
                        + next_layer
                        * self.p.add_position_threshold
                        * (upper_band - lower_band)
                    )
                    if spread > add_threshold:
                        self._add_position(short=True)
            # Close position logic
            if pos > 0 and spread >= mid_band:  # Holding long position and spread reverts to median
                self._close_positions()
            elif pos < 0 and spread <= mid_band:  # Holding short position and spread reverts to median
                self._close_positions()

    def _open_position(self, short):
        """Dynamic ratio order placement"""
        # Confirm trading size is valid
        if not hasattr(self, "size0") or not hasattr(self, "size1"):
            self.size0 = 10  # Default value
            self.size1 = (
                round(self.data2.beta[0] * 10)
                if not pd.isna(self.data2.beta[0])
                else 14
            )

        # Check if there are sufficient funds
        cash = self.broker.getcash()
        cost = self.size0 * self.data0.close[0] + self.size1 * self.data1.close[0]
        if cash < cost:
            if self.p.verbose:
                print(f"Insufficient funds, cannot open position: need {cost:.2f}, available {cash:.2f}")
            return

        if short:
            if self.p.verbose:
                print(f"Long J {self.size0} lots, Short JM {self.size1} lots")
            self.buy(data=self.data0, size=self.size0)
            self.sell(data=self.data1, size=self.size1)
            self.entry_direction = "short"
        else:
            if self.p.verbose:
                print(f"Short J {self.size0} lots, Long JM {self.size1} lots")
            self.sell(data=self.data0, size=self.size0)
            self.buy(data=self.data1, size=self.size1)
            self.entry_direction = "long"
        self.entry_price = self.data2.close[0]
        self.position_layers = 1  # First position is the first layer

    def _add_position(self, short):
        """Add position, automatic arbitrage ratio, fund check"""
        # Calculate position sizing (equal size for each layer, can also be customized to decrease)
        add_size0 = self.size0
        add_size1 = self.size1
        # Check available funds
        cash = self.broker.getcash()
        cost = add_size0 * self.data0.close[0] + add_size1 * self.data1.close[0]
        if cash < cost:
            if self.p.verbose:
                print(f"Insufficient funds, cannot add position: need {cost:.2f}, available {cash:.2f}")
            return
        if short:
            # if self.p.verbose:
            print(f"Adding position: long J {add_size0} lots, short JM {add_size1} lots")
            self.buy(data=self.data0, size=add_size0)
            self.sell(data=self.data1, size=add_size1)
        else:
            # if self.p.verbose:
            print(f"Adding position: short J {add_size0} lots, long JM {add_size1} lots")
            self.sell(data=self.data0, size=add_size0)
            self.buy(data=self.data1, size=add_size1)
        self.position_layers += 1

    def _close_positions(self):
        self.close(data=self.data0)
        self.close(data=self.data1)
        self.position_layers = 0  # Reset position layers after closing

    def notify_trade(self, trade):
        if not self.p.verbose:
            return

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
                % (
                    trade.ref,
                    bt.num2date(trade.dtopen),
                    trade.size,
                    trade.value,
                )
            )


def run_strategy(
    data0,
    data1,
    data2,
    lookback_period,
    upper_quantile,
    lower_quantile,
    spread_window=60,
):
    """运行单次回测"""
    # 创建回测引擎
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(data0, name="data0")
    cerebro.adddata(data1, name="data1")
    cerebro.adddata(data2, name="spread")

    # 添加策略
    cerebro.addstrategy(
        DynamicSpreadQuantileStrategy,
        lookback_period=lookback_period,
        upper_quantile=upper_quantile,
        lower_quantile=lower_quantile,
        verbose=False,
    )

    # 设置初始资金
    cerebro.broker.setcash(100000)
    cerebro.broker.set_shortcash(False)

    # 添加分析器
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        timeframe=bt.TimeFrame.Days,
        riskfreerate=0,
        annualize=True,
    )
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.Returns)
    cerebro.addanalyzer(bt.analyzers.ROIAnalyzer, period=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

    # 运行回测
    results = cerebro.run()

    # 获取分析结果
    strat = results[0]
    sharpe = strat.analyzers.sharperatio.get_analysis().get("sharperatio", 0)
    drawdown = strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0)
    returns = strat.analyzers.returns.get_analysis().get("rnorm100", 0)
    roi = strat.analyzers.roianalyzer.get_analysis().get("roi100", 0)
    trades = strat.analyzers.tradeanalyzer.get_analysis().get("total", 0)

    return {
        "sharpe": sharpe,
        "drawdown": drawdown,
        "returns": returns,
        "roi": roi,
        "trades": trades,
        "params": {
            "period": lookback_period,
            "upper_quantile": upper_quantile,
            "lower_quantile": lower_quantile,
            "spread_window": spread_window,
        },
    }


def grid_search():
    """执行网格搜索找到最优参数"""
    # 读取数据
    output_file = "/Users/f/Desktop/ricequant/1d_2017to2024_noadjust.h5"
    df0 = pd.read_hdf(output_file, key="/J").reset_index()
    df1 = pd.read_hdf(output_file, key="/JM").reset_index()

    # 确保日期列格式正确
    df0["date"] = pd.to_datetime(df0["date"])
    df1["date"] = pd.to_datetime(df1["date"])

    fromdate = datetime.datetime(2018, 1, 1)
    todate = datetime.datetime(2025, 1, 1)

    # Define parameter grid
    lookback_periods = [30]
    upper_quantiles = [0.8]
    spread_windows = [60]  # Added: spread calculation window parameter

    # Calculate corresponding lower_quantile for each upper_quantile
    param_combinations = []
    for spread_window in spread_windows:
        # Calculate rolling spread for the current window
        print(f"Calculating rolling spread (window={spread_window})...")
        df_spread = calculate_rolling_spread(df0, df1, window=spread_window)

        # Add data
        data0 = bt.feeds.PandasData(
            dataname=df0,
            datetime="date",
            nocase=True,
            fromdate=fromdate,
            todate=todate,
        )
        data1 = bt.feeds.PandasData(
            dataname=df1,
            datetime="date",
            nocase=True,
            fromdate=fromdate,
            todate=todate,
        )
        data2 = SpreadData(dataname=df_spread, fromdate=fromdate, todate=todate)

        for period in lookback_periods:
            for upper_q in upper_quantiles:
                lower_q = 1 - upper_q  # 对称设置
                param_combinations.append(
                    (
                        data0,
                        data1,
                        data2,
                        period,
                        upper_q,
                        lower_q,
                        spread_window,
                    )
                )

    # 执行网格搜索
    results = []
    total_combinations = len(param_combinations)

    print(f"开始网格搜索，共{total_combinations}种参数组合...")

    for i, (
        data0,
        data1,
        data2,
        period,
        upper_q,
        lower_q,
        spread_window,
    ) in enumerate(param_combinations):
        print(
            f"测试参数组合 {i + 1}/{total_combinations}: period={period},"
            f" upper_q={upper_q:.2f}, lower_q={lower_q:.2f},"
            f" spread_window={spread_window}"
        )

        try:
            result = run_strategy(
                data0, data1, data2, period, upper_q, lower_q, spread_window
            )
            results.append(result)

            # 打印当前结果
            print(
                f"  夏普比率: {result['sharpe']:.4f}, 最大回撤:"
                f" {result['drawdown']:.2f}%, 年化收益: {result['returns']:.2f}%，"
                f"交易次数: {result['trades']}"
            )
        except Exception as e:
            print(f"  参数组合出错: {e}")

    # 找出最佳参数组合
    if results:
        # 按夏普比率排序
        sorted_results = sorted(
            results,
            key=lambda x: (x["sharpe"] if x["sharpe"] is not None else -float("inf")),
            reverse=True,
        )
        best_result = sorted_results[0]

        print("\n========= Best Parameter Combination =========")
        print(f"Spread calculation window: {best_result['params']['spread_window']}")
        print(f"Lookback period: {best_result['params']['period']}")
        print(f"Upper quantile: {best_result['params']['upper_quantile']:.2f}")
        print(f"Lower quantile: {best_result['params']['lower_quantile']:.2f}")
        print(f"Sharpe ratio: {best_result['sharpe']:.4f}")
        print(f"Maximum drawdown: {best_result['drawdown']:.2f}%")
        print(f"Annual return: {best_result['returns']:.2f}%")
        print(f"Total ROI: {best_result['roi']:.2f}%")

        # Display all results, sorted by Sharpe ratio
        print("\n========= All Parameter Combinations (sorted by Sharpe ratio) =========")
        for i, result in enumerate(sorted_results[:10]):  # Only show top 10 best results
            print(
                f"{i + 1}. spread_window={result['params']['spread_window']}, "
                f"period={result['params']['period']}, "
                f"upper_q={result['params']['upper_quantile']:.2f}, "
                f"lower_q={result['params']['lower_quantile']:.2f}, "
                f"sharpe={result['sharpe']:.4f}, "
                f"drawdown={result['drawdown']:.2f}%, "
                f"return={result['returns']:.2f}%"
            )
    else:
        print("未找到有效的参数组合")


# 创建自定义数据类以支持beta列
class SpreadData(bt.feeds.PandasData):
    lines = ("beta",)  # 添加beta线

    params = (
        ("datetime", "date"),  # 日期列
        ("close", "close"),  # 价差列作为close
        ("beta", "beta"),  # beta列
        ("nocase", True),  # 列名不区分大小写
    )


if __name__ == "__main__":
    grid_search()
