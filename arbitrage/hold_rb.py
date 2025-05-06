# Copyright (c) 2025 backtrader contributors
"""
Always-hold strategy for rebar (螺纹钢) using Backtrader. This module demonstrates
how to set up a simple strategy that always holds a position in rebar futures and
analyzes the results using several built-in analyzers.
"""


import pandas as pd
import backtrader as bt
from backtrader.analyzers.drawdown import DrawDown
from backtrader.analyzers.sharpe import SharpeRatio
from backtrader.analyzers.returns import Returns
from backtrader.analyzers.tradeanalyzer import TradeAnalyzer
from backtrader.analyzers.caganalyzer import CAGRAnalyzer


# 始终持有螺纹钢策略
class AlwaysHoldRBStrategy(bt.Strategy):
    """A Backtrader strategy that always holds a position in rebar (螺纹钢).
Parameters
----------
size_rb : int, optional
The trading size for rebar contracts (default is 1)."""

    params = ("size_rb", 1)

    def __init__(self):
        """
        Initialize the AlwaysHoldRBStrategy. Ensures the parent class is properly
        initialized and sets up the order tracking attribute.
        """
        super().__init__()
        self.order = None

    def next(self):
        """
        Called on each new bar. Always holds a position in rebar by buying if not
        already in a position.
        """
        if not self.position:
            self.order = self.buy(
                data=self.data0, size=self.p.size_rb, price=self.data0.close[0]
            )
            print(
                f"下单价格: {self.data0.close[0]}, 时间: "
                f"{self.data0.datetime.datetime()}, 持仓: {self.position}"
            )

    def notify_order(self, order):
        """Receives order notifications and resets the order attribute when the order
is completed, canceled, or has a margin issue.
Parameters
----------
order : bt.Order
The order object being notified."""
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None


# 读取数据
output_file = "D://y5//RB_daily.h5"
df_RB = pd.read_hdf(output_file, key="data")

# 确保 'date' 列转换为 datetime 类型
df_RB["date"] = pd.to_datetime(df_RB["date"], errors="coerce")

from backtrader.feeds import PandasData

data1 = PandasData(dataname=df_RB)

# 创建回测引擎
cerebro = bt.Cerebro()

cerebro.adddata(data1, name="RB")

# 添加策略
cerebro.addstrategy(AlwaysHoldRBStrategy)

# 设置初始资金
# cerebro.broker.setcash(1000000.0)

# 添加分析器：SharpeRatio、DrawDown、Returns 和 TradeAnalyzer
cerebro.addanalyzer(DrawDown, _name="drawdown")
cerebro.addanalyzer(SharpeRatio, _name="sharperatio")
cerebro.addanalyzer(Returns, _name="returns")
cerebro.addanalyzer(TradeAnalyzer, _name="tradeanalyzer")

# 添加CAGR分析器
cerebro.addanalyzer(CAGRAnalyzer, period=bt.TimeFrame.Days)

# 运行回测
results = cerebro.run()

# 获取分析结果
sharpe = results[0].analyzers.sharperatio.get_analysis()
drawdown = results[0].analyzers.drawdown.get_analysis()
total_returns = results[0].analyzers.returns.get_analysis()
trade = results[0].analyzers.tradeanalyzer.get_analysis()
# 打印分析结果
print(f"\n夏普比率: {sharpe['sharperatio']}")
print(f"最大回撤: {drawdown['max']['drawdown']} %")
print(f"总回报率: {total_returns['rnorm100']:.2f}%")  # 打印总回报率

# 绘制结果
# cerebro.plot(volume=False)
