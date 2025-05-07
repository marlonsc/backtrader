"""caganalyzer.py module.

Description of the module functionality."""

import matplotlib.pyplot as plt
import numpy as np
from backtrader import TimeFrameAnalyzerBase


class CAGRAnalyzer(TimeFrameAnalyzerBase):
    """Calculates the Compound Annual Growth Rate (CAGR) and plots cumulative returns."""

    params = (
        ("period", None),
        ("fund", None),
        ("plot", True),  # New parameter: whether to automatically plot
    )

    _TANN = {
        bt.TimeFrame.Days: 252.0,
        bt.TimeFrame.Weeks: 52.0,
        bt.TimeFrame.Months: 12.0,
        bt.TimeFrame.Years: 1.0,
    }

    def __init__(self):
""""""
""""""
""""""
        """Calculate returns on each time step"""
        # 计算每个时间步骤的收益率

        # if self._value_start != 0.0:

        # current_value = self.strategy.broker.getvalue() if not self._fundmode else self.strategy.broker.fundvalue
        current_value = self.strategy.broker.getvalue()

        # 分子分母为0
        daily_return = (
            0 if self._value_start == 0 else (current_value / self._value_start) - 1
        )
        daily_return = 0 if daily_return == -1 else daily_return

        self._returns.append(daily_return)  # 将当前时间的收益率存储起来

        # 累乘每日收益率
        self._cum_return *= 1 + daily_return

        # 记录日期和累积收益率
        self.dates.append(self.strategy.datetime.date())
        self.cum_returns.append(self._cum_return)

        # print(self._cum_return,daily_return,self.strategy.broker._valuemkt,self.strategy.broker.getvalue(),self.strategy.broker.getcash())

        # 更新初始值（当新的时间段（天、周、月等）开始时，使用当前值作为新的初始值）
        # self._value_start = self.strategy.broker.getvalue() if not self._fundmode else self.strategy.broker.fundvalue
        self._value_start = self.strategy.broker.getvalue()

    def plot_cumulative_returns(self):
        """绘制累积收益率图表"""
        plt.figure(figsize=(10, 6))
        plt.plot(self.dates, self.cum_returns, "b-", linewidth=2)
        plt.title("cumulative returns")
        plt.xlabel("date")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def get_analysis(self):
        """Returns the CAGR value"""

        return self.rets
