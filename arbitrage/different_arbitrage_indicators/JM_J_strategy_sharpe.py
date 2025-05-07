# Copyright (c) 2025 backtrader contributors
"""Sharpe difference Bollinger Band strategy for J/JM futures. Includes data loading,
strategy logic, and result analysis with plotting."""
"""
import datetime

import backtrader as bt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from arbitrage.common_strategy_utils import (
    init_common_vars,
    notify_order_default,
    notify_trade_default,
)
from backtrader.analyzers.drawdown import DrawDown
from backtrader.analyzers.sharpe import SharpeRatio
from backtrader.analyzers.timereturn import TimeReturn


# 夏普差值布林带策略
class SharpeDiffStrategy(bt.Strategy):
""""""
""""""
""""""
""""""
""""""
"""Args::
    symbol1: 
    symbol2: 
    fromdate: 
    todate:"""
    todate:"""
    output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"

    try:
        # 加载数据时不保留原有索引结构
        df0 = pd.read_hdf(output_file, key=symbol1).reset_index()
        df1 = pd.read_hdf(output_file, key=symbol2).reset_index()

        # 查找日期列（兼容不同命名）
        date_col = [col for col in df0.columns if "date" in col.lower()]
        if not date_col:
            raise ValueError("数据集中未找到日期列")

        # 设置日期索引
        df0 = df0.set_index(pd.to_datetime(df0[date_col[0]]))
        df1 = df1.set_index(pd.to_datetime(df1[date_col[0]]))
        df0 = df0.sort_index().loc[fromdate:todate]
        df1 = df1.sort_index().loc[fromdate:todate]

        # Create data feeds
        data0 = bt.feeds.PandasData(df0)
        data1 = bt.feeds.PandasData(df1)
        return data0, data1
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None, None


# 配置回测引擎
def configure_cerebro(**kwargs):
    """"""
    cerebro = bt.Cerebro()
    data0, data1 = load_data(
        "/J",
        "/JM",
        datetime.datetime(2017, 1, 1),
        datetime.datetime(2025, 1, 1),
    )

    if data0 is None or data1 is None:
        print("无法加载数据，请检查文件路径和数据格式")
        return None

    cerebro.adddata(data0, name="J")
    cerebro.adddata(data1, name="JM")
    cerebro.addstrategy(SharpeDiffStrategy, printlog=True)
    cerebro.broker.setcash(80000)
    cerebro.broker.set_shortcash(False)
    cerebro.addanalyzer(DrawDown)
    cerebro.addanalyzer(SharpeRatio)
    cerebro.addanalyzer(TimeReturn)
    return cerebro


def analyze_results(results):
"""Args::
    results:"""
    results:"""
    if not results:
        print("没有回测结果可分析")
        return

    try:
        drawdown = results[0].analyzers.drawdown.get_analysis()
        sharpe = results[0].analyzers.sharperatio.get_analysis()
        returns = results[0].analyzers.timereturn.get_analysis()
        print("=============回测结果================")
        print(f"Sharpe Ratio: {sharpe.get('sharperatio', 0):.2f}")
        print(f"Drawdown: {drawdown.get('max', {}).get('drawdown', 0):.2f} %")
        print(f"Total return: {returns.get('rtot', 0):.2%}")
    except Exception as e:
        print(f"分析结果时出错: {e}")


if __name__ == "__main__":
    cerebro = configure_cerebro()
    if cerebro:
        print("开始回测...")
        strats = cerebro.run()  # pylint: disable=no-member
        analyze_results(strats)
        cerebro.plot()
