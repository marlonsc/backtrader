"""hold_rb.py module.

Description of the module functionality."""

import pandas as pd

# 设置显示选项，不使用省略号
pd.set_option("display.max_columns", None)  # 显示所有列
pd.set_option("display.max_colwidth", None)  # 显示列的完整内容


# 始终持有螺纹钢策略
class AlwaysHoldRBStrategy(bt.Strategy):
""""""
""""""
""""""
""""""
""""""
"""Args::
    trade:"""
"""Args::
    order:"""
    order:"""
        if order.status in [order.Submitted, order.Accepted]:
            # 订单状态 submitted/accepted，处于未决订单状态。
            return

        # 订单已决，执行如下语句
        if order.status in [order.Completed]:
            if order.isbuy():
                print(
                    f"executed date {self.data.datetime.date(0)},executed price {
                        order.executed.price
                    }, created date {self.data.datetime.date(0)}"
                )


# 读取数据
output_file = "D://y5//RB_daily.h5"
df_RB = pd.read_hdf(output_file, key="data")

# 确保 'date' 列转换为 datetime 类型
df_RB["date"] = pd.to_datetime(df_RB["date"], errors="coerce")

# 检查数据头部
print(df_RB.head())


data1 = bt.feeds.PandasData(dataname=df_RB)

# 创建回测引擎
cerebro = bt.Cerebro()

cerebro.adddata(data1, name="RB")

# 添加策略
cerebro.addstrategy(AlwaysHoldRBStrategy)

# 设置初始资金
cerebro.broker.setcash(1000.0)
cerebro.broker.set_shortcash(False)
# 添加分析器：SharpeRatio、DrawDown、AnnualReturn 和 Returns
cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharperatio")
cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="tradeanalyzer")

cerebro.addanalyzer(
    bt.analyzers.CAGRAnalyzer, period=bt.TimeFrame.Days
)  # 这里的period可以是daily, weekly, monthly等
# 运行回测
results = cerebro.run()

# 获取分析结果
sharpe = results[0].analyzers.sharperatio.get_analysis()
drawdown = results[0].analyzers.drawdown.get_analysis()
total_returns = results[0].analyzers.returns.get_analysis()
trade = results[0].analyzers.tradeanalyzer.get_analysis()

# 打印分析结果
print("=============回测结果================")
print(f"\n夏普比率: {sharpe['sharperatio']:.2f}")
print(f"最大回撤: {drawdown['max']['drawdown']:.2f} %")
print(f"总回报率: {total_returns['rnorm100']:.2f}%")  # 打印总回报率

print(f"交易记录: {trade}")

# # 打印年度回报率
# print("\n年度回报率:")
# print("=" * 80)
# print("{:<8} {:<12}".format("年份", "回报率"))
# for year, return_rate in annual_returns.items():
#     print("{:<8} {:<12.2%}".format(year, return_rate))

# 绘制结果
cerebro.plot(volume=False)
