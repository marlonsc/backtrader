# Copyright (c) 2025 backtrader contributors
"""
Grid search for CUSUM/Z-Score pair trading strategy for J/JM futures. Includes
rolling beta spread calculation, parameter optimization, and result visualization.
"""
import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import backtrader as bt
from backtrader.indicators.deviation import StandardDeviation as StdDev
from backtrader.analyzers.drawdown import DrawDown
from backtrader.analyzers.sharpe import SharpeRatio
from backtrader.analyzers.returns import Returns
from backtrader.analyzers.roi import ROIAnalyzer
from backtrader.analyzers.tradeanalyzer import TradeAnalyzer


def calculate_rolling_spread(
    df0: pd.DataFrame,  # 必含 'date' 与价格列
    df1: pd.DataFrame,
    window: int = 30,
    fields=("open", "high", "low", "close"),
) -> pd.DataFrame:
    """计算滚动 β，并为指定价格字段生成价差 (spread)：
spread_x = price0_x - β_{t-1} * price1_x"""
    # 1) 用收盘价对齐合并（β 仍用 close 估计）
    df = (
        df0.set_index("date")[["close"]]
        .rename(columns={"close": "close0"})
        .join(
            df1.set_index("date")[["close"]].rename(columns={"close": "close1"}),
            how="inner",
        )
    )

    # 2) 估计 β_t ，再向前挪一天
    beta_raw = (
        df["close0"].rolling(window).cov(df["close1"])
        / df["close1"].rolling(window).var()
    )
    beta_shift = beta_raw.shift(1).round(1)  # 防未来 + 保留 1 位小数

    # 3) 把 β 拼回主表（便于后面 vectorized 计算）
    df = df.assign(beta=beta_shift)

    # 4) 对每个字段算 spread
    out_cols = {"date": df.index, "beta": beta_shift}
    for f in fields:
        if f not in ("open", "high", "low", "close"):
            raise ValueError(f"未知字段 {f}")
        p0 = df0.set_index("date")[f]
        p1 = df1.set_index("date")[f]
        aligned = p0.to_frame(name=f"price0_{f}").join(
            p1.to_frame(name=f"price1_{f}"), how="inner"
        )
        spread_f = aligned[f"price0_{f}"] - beta_shift * aligned[f"price1_{f}"]
        out_cols[f"{f}"] = spread_f

    # 5) 整理输出
    out = pd.DataFrame(out_cols).dropna().reset_index(drop=True)
    out["date"] = pd.to_datetime(out["date"])
    return out


# 创建自定义数据类以支持beta列
class SpreadData(bt.feeds.PandasData):
    lines = ("beta",)  # 添加beta线

    params = (
        ("datetime", "date"),  # 日期列
        ("close", "close"),  # 价差列作为close
        ("beta", "beta"),  # beta列
        ("nocase", True),  # 列名不区分大小写
    )


class DynamicSpreadZScoreStrategy(bt.Strategy):
    params = (
        ("win", 20),  # 计算均值和标准差的窗口
        ("entry_zscore", 2.0),  # 入场Z-Score阈值
        ("exit_zscore", 0.5),  # 出场Z-Score阈值
        ("verbose", False),  # 是否打印详细信息
    )

    def __init__(self):
        # 方便读取最近 win 根价差
        self.spread_series = self.data2.close
        # 计算价差的滚动均值和标准差
        self.mean = bt.indicators.SMA(self.spread_series, period=self.p.win)
        self.stddev = bt.indicators.StdDev(self.spread_series, period=self.p.win)

    # ---------- 交易辅助（沿用原有逻辑） ----------
    def _open_position(self, short):
        if not hasattr(self, "size0"):
            self.size0 = 10
            self.size1 = round(self.data2.beta[0] * 10)
        if short:  # 做空价差
            self.sell(data=self.data0, size=self.size0)
            self.buy(data=self.data1, size=self.size1)
        else:  # 做多价差
            self.buy(data=self.data0, size=self.size0)
            self.sell(data=self.data1, size=self.size1)

    def _close_positions(self):
        self.close(data=self.data0)
        self.close(data=self.data1)

    # ---------- 主循环 ----------
    def next(self):
        # 1) 确保有足够历史用于计算均值和标准差
        if len(self.spread_series) < self.p.win + 2:
            return

        # 2) 计算当前价差的Z-Score
        if self.stddev[0] == 0:
            return

        z_score = (self.spread_series[0] - self.mean[0]) / self.stddev[0]

        position_size = self.getposition(self.data0).size

        # 3) 交易逻辑
        if position_size == 0:  # 当前无持仓
            # 计算动态配比
            beta_now = self.data2.beta[0]
            if pd.isna(beta_now) or beta_now <= 0:
                return
            self.size0 = 10
            self.size1 = round(beta_now * 10)

            if (
                z_score > self.p.entry_zscore
            ):  # 价差大于 entry_zscore 个标准差 → 做空价差
                self._open_position(short=True)
            elif (
                z_score < -self.p.entry_zscore
            ):  # 价差小于 -entry_zscore 个标准差 → 做多价差
                self._open_position(short=False)
        else:  # 当前有持仓，考虑平仓
            if (
                position_size > 0 and z_score > -self.p.exit_zscore
            ):  # 做多价差的平仓条件
                self._close_positions()
            elif (
                position_size < 0 and z_score < self.p.exit_zscore
            ):  # 做空价差的平仓条件
                self._close_positions()

    def notify_trade(self, trade):
        if not self.p.verbose:
            return

        if trade.isclosed:
            print(
                f"TRADE {trade.ref} CLOSED, PROFIT: GROSS {trade.pnl:.2f}, NET {
                    trade.pnlcomm:.2f
                }, PRICE {trade.value}"
            )
        elif trade.justopened:
            print(
                f"TRADE {trade.ref} OPENED {trade.dtopen}, SIZE {trade.size}, PRICE {
                    trade.value
                }"
            )


def run_strategy(data0, data1, data2, win, entry_zscore, exit_zscore, spread_window=60):
    """运行单次回测"""
    # 创建回测引擎
    cerebro = bt.Cerebro()
    cerebro.adddata(data0, name="data0")
    cerebro.adddata(data1, name="data1")
    cerebro.adddata(data2, name="spread")

    # 添加策略
    cerebro.addstrategy(
        DynamicSpreadZScoreStrategy,
        win=win,
        entry_zscore=entry_zscore,
        exit_zscore=exit_zscore,
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
    trades = strat.analyzers.tradeanalyzer.get_analysis()

    # 获取交易统计
    total_trades = trades.get("total", {}).get("total", 0)
    win_trades = trades.get("won", {}).get("total", 0)
    loss_trades = trades.get("lost", {}).get("total", 0)
    win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0

    return {
        "sharpe": sharpe,
        "drawdown": drawdown,
        "returns": returns,
        "roi": roi,
        "total_trades": total_trades,
        "win_trades": win_trades,
        "loss_trades": loss_trades,
        "win_rate": win_rate,
        "params": {
            "win": win,
            "entry_zscore": entry_zscore,
            "exit_zscore": exit_zscore,
            "spread_window": spread_window,
        },
    }


def plot_heatmap(results, output_file="zscore_heatmap.png"):
    """绘制热力图展示不同参数组合的夏普比率"""
    if len(results) == 0:
        print("没有有效结果，无法绘制热力图")
        return

    # 创建结果DataFrame
    df_results = pd.DataFrame(results)

    # 为每个exit_zscore创建一个子图
    exit_zscores = sorted(
        df_results["params"].apply(lambda x: x["exit_zscore"]).unique()
    )
    spread_windows = sorted(
        df_results["params"].apply(lambda x: x["spread_window"]).unique()
    )

    # 计算子图布局
    n_plots = len(exit_zscores)
    n_cols = min(3, n_plots)
    n_rows = (n_plots + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
    if n_rows == 1 and n_cols == 1:
        axes = np.array([axes])
    elif n_rows == 1 or n_cols == 1:
        axes = axes.flatten()

    for i, exit_zscore in enumerate(exit_zscores):
        row, col = i // n_cols, i % n_cols
        ax = axes[row, col] if n_rows > 1 and n_cols > 1 else axes[i]

        # 过滤数据
        e_data = df_results[
            df_results["params"].apply(lambda x: x["exit_zscore"]) == exit_zscore
        ]

        for spread_window in spread_windows:
            # 进一步过滤特定的spread_window
            sw_data = e_data[
                e_data["params"].apply(lambda x: x["spread_window"]) == spread_window
            ]

            # 提取win和entry_zscore
            pivot_data = pd.DataFrame(
                {
                    "win": sw_data["params"].apply(lambda x: x["win"]),
                    "entry_zscore": (
                        sw_data["params"].apply(lambda x: x["entry_zscore"])
                    ),
                    "sharpe": sw_data["sharpe"],
                }
            )

            # 创建透视表
            pivot = pivot_data.pivot_table(
                values="sharpe",
                index="win",
                columns="entry_zscore",
                aggfunc="mean",
            )

            # 绘制热力图
            sns.heatmap(
                pivot,
                annot=True,
                fmt=".2f",
                cmap="YlGnBu",
                ax=ax,
                cbar_kws={"label": "Sharpe Ratio"},
            )

            ax.set_title(f"exit_zscore={exit_zscore}, spread_window={spread_window}")
            ax.set_xlabel("entry_zscore")
            ax.set_ylabel("win")

    plt.tight_layout()
    plt.savefig(output_file)
    print(f"热力图已保存至 {output_file}")


def grid_search():
    """执行网格搜索找到最优参数"""
    # 读取数据
    output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"
    df0 = pd.read_hdf(output_file, key="/J").reset_index()
    df1 = pd.read_hdf(output_file, key="/JM").reset_index()

    # 确保日期列格式正确
    df0["date"] = pd.to_datetime(df0["date"])
    df1["date"] = pd.to_datetime(df1["date"])

    fromdate = datetime.datetime(2018, 1, 1)
    todate = datetime.datetime(2025, 1, 1)

    # 定义参数网格
    win_values = [15, 20, 30, 60]  # 计算均值和标准差的窗口
    entry_zscore_values = [1.5, 2.0, 2.5, 3.0]  # 入场Z-Score阈值
    exit_zscore_values = [0.0, 0.5, 1.0]  # 出场Z-Score阈值
    spread_windows = [20, 30, 60]  # 价差计算窗口

    # 生成参数组合
    param_combinations = []
    for spread_window in spread_windows:
        # 计算当前窗口下的滚动价差
        print(f"计算滚动价差 (window={spread_window})...")
        df_spread = calculate_rolling_spread(df0, df1, window=spread_window)

        # 添加数据
        data0 = bt.feeds.PandasData(df0)
        data1 = bt.feeds.PandasData(df1)
        data2 = SpreadData(df_spread)

        for win in win_values:
            for entry_zscore in entry_zscore_values:
                for exit_zscore in exit_zscore_values:
                    param_combinations.append(
                        (
                            data0,
                            data1,
                            data2,
                            win,
                            entry_zscore,
                            exit_zscore,
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
        win,
        entry_zscore,
        exit_zscore,
        spread_window,
    ) in enumerate(param_combinations):
        print(
            f"测试参数组合 {i + 1}/{total_combinations}: win={win},"
            f" entry_zscore={entry_zscore:.1f}, exit_zscore={exit_zscore:.1f},"
            f" spread_window={spread_window}"
        )

        try:
            result = run_strategy(
                data0,
                data1,
                data2,
                win,
                entry_zscore,
                exit_zscore,
                spread_window,
            )
            results.append(result)

            # 打印当前结果
            print(
                f"  夏普比率: {result['sharpe']:.4f}, 最大回撤:"
                f" {result['drawdown']:.2f}%, 年化收益: {result['returns']:.2f}%, 胜率:"
                f" {result['win_rate']:.2f}%"
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

        print("\n========= 最佳参数组合 =========")
        print(f"价差计算窗口: {best_result['params']['spread_window']}")
        print(f"Rolling窗口 (win): {best_result['params']['win']}")
        print(
            "入场Z-Score阈值 (entry_zscore):"
            f" {best_result['params']['entry_zscore']:.2f}"
        )
        print(
            f"出场Z-Score阈值 (exit_zscore): {best_result['params']['exit_zscore']:.2f}"
        )
        print(f"夏普比率: {best_result['sharpe']:.4f}")
        print(f"最大回撤: {best_result['drawdown']:.2f}%")
        print(f"年化收益: {best_result['returns']:.2f}%")
        print(f"总收益率: {best_result['roi']:.2f}%")
        print(f"总交易次数: {best_result['total_trades']}")
        print(f"胜率: {best_result['win_rate']:.2f}%")

        # 绘制热力图
        plot_heatmap(results)

        # 显示所有结果，按夏普比率排序
        print("\n========= 所有参数组合结果（按夏普比率排序）=========")
        for i, result in enumerate(sorted_results[:10]):  # 只显示前10个最好的结果
            print(
                f"{i + 1}. spread_window={result['params']['spread_window']}, "
                f"win={result['params']['win']}, "
                f"entry_zscore={result['params']['entry_zscore']:.2f}, "
                f"exit_zscore={result['params']['exit_zscore']:.2f}, "
                f"sharpe={result['sharpe']:.4f}, "
                f"drawdown={result['drawdown']:.2f}%, "
                f"return={result['returns']:.2f}%, "
                f"win_rate={result['win_rate']:.2f}%"
            )
    else:
        print("未找到有效的参数组合")


if __name__ == "__main__":
    grid_search()
