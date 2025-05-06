"""JM_J_strategy_skewness_grid.py module.

Description of the module functionality."""


import backtrader as bt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns  # pylint: disable=import-error


# 偏度差均值回归策略（基于历史统计量的版本）
class SkewnessArbitrageStrategy(bt.Strategy):
""""""
""""""
""""""
"""Args::
    order:"""
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

        # Create data feeds using 'dataname' for compatibility
        data0 = bt.feeds.PandasData()
        data0.dataname = df0
        data1 = bt.feeds.PandasData()
        data1.dataname = df1
        return data0, data1
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None, None


# 运行网格回测并绘制热力图
def run_grid_search():
""""""
    # 定义参数网格
    skew_periods = range(10, 41, 5)  # 10, 15, 20, 25, 30, 35, 40
    entry_multipliers = [0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0]

    # 存储结果
    results = np.zeros((len(skew_periods), len(entry_multipliers)))

    # 设置初始日期
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)

    # 加载数据一次（这些数据可以重复使用）
    data0, data1 = load_data("/J", "/JM", fromdate, todate)

    if data0 is None or data1 is None:
        print("无法加载数据，请检查文件路径和数据格式")
        return

    print("开始网格回测...")
    print(
        f"测试参数组合: {len(skew_periods)} x {len(entry_multipliers)} ="
        f" {len(skew_periods) * len(entry_multipliers)}个组合"
    )

    # 进行网格回测
    for i, skew_period in enumerate(skew_periods):
        for j, entry_multiplier in enumerate(entry_multipliers):
            print(
                f"测试参数: skew_period={skew_period},"
                f" entry_std_multiplier={entry_multiplier}"
            )

            # 创建一个新的cerebro实例
            cerebro = bt.Cerebro()

            # 添加相同的数据
            cerebro.adddata(data0, name="J")
            cerebro.adddata(data1, name="JM")

            # 添加策略，使用当前测试的参数
            cerebro.addstrategy(
                SkewnessArbitrageStrategy,
                skew_period=skew_period,
                entry_std_multiplier=entry_multiplier,
                printlog=False,
            )  # 关闭日志，减少输出

            # 设置资金和佣金
            cerebro.broker.setcash(100000)
            cerebro.broker.setcommission(commission=0.0003)

            cerebro.broker.set_shortcash(False)

            # 添加夏普比率分析器
            try:
                cerebro.addanalyzer(
                    bt.analyzers.SharpeRatio,
                    timeframe=bt.TimeFrame.Days,
                    riskfreerate=0,
                    annualize=True,
                )
            except AttributeError:
                pass  # pylint: disable=import-error

            # 运行回测
            try:
                strats = cerebro.run()
            except AttributeError:
                cerebro.prerun()
                cerebro.startrun()
                strats = cerebro.finishrun()

            # 获取夏普比率
            sharpe = (
                strats[0].analyzers.sharperatio.get_analysis().get("sharperatio", 0)
            )

            # 存储结果
            results[i, j] = sharpe

            print(f"夏普比率: {sharpe:.2f}")

    # 绘制热力图
    plt.figure(figsize=(12, 8))

    # 使用Seaborn的热力图
    ax = sns.heatmap(
        results,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        xticklabels=entry_multipliers,
        yticklabels=skew_periods,
    )

    # 设置标题和标签
    plt.title("sharperatio - skew_period vs entry_std_multiplier")
    plt.xlabel("entry_std_multiplier")
    plt.ylabel("skew_period")

    # 显示图形
    plt.tight_layout()
    plt.savefig("sharpe_ratio_heatmap.png")
    plt.show()

    print("热力图已保存为 'sharpe_ratio_heatmap.png'")

    # Find best parameter combination
    max_i, max_j = np.unravel_index(int(results.argmax()), results.shape)
    max_i = int(max_i)
    max_j = int(max_j)
    best_skew_period = skew_periods[max_i]
    best_entry_multiplier = entry_multipliers[max_j]
    best_sharpe = results[max_i, max_j]

    print("\n最佳参数组合:")
    print(f"skew_period: {best_skew_period}")
    print(f"entry_std_multiplier: {best_entry_multiplier}")
    print(f"sharperatio: {best_sharpe:.4f}")

    return results, skew_periods, entry_multipliers


# 修改主函数，调用网格搜索
if __name__ == "__main__":
    run_grid_search()
