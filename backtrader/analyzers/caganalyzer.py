import math
import pandas as pd
import numpy as np
import backtrader as bt
import matplotlib.pyplot as plt
from collections import OrderedDict
from backtrader import TimeFrameAnalyzerBase
import matplotlib.pyplot as mpyplot

class CAGRAnalyzer(TimeFrameAnalyzerBase):
    '''Calculates the Compound Annual Growth Rate (CAGR) and plots cumulative returns.

    Params:
      - ``period`` (default: ``daily``): Annualization period (daily/weekly/monthly/yearly)
      - ``fund`` (default: ``None``): Fund mode (True/False), None for auto-detect
      - ``plot`` (default: ``True``): Whether to auto-generate cumulative return plot
    '''

    params = (
        ('period', None),
        ('fund', None),
        ('plot', True),  # 新增参数：是否自动绘图
    )

    _TANN = {
        bt.TimeFrame.Days: 252.0,
        bt.TimeFrame.Weeks: 52.0,
        bt.TimeFrame.Months: 12.0,
        bt.TimeFrame.Years: 1.0,
    }

    def __init__(self):
        # 初始化数据容器
        self.dates = []  # 记录每个bar的日期
        self.cum_returns = []  # 记录每日累计收益率
        self._returns = []  # 记录每日收益率
        super(CAGRAnalyzer, self).__init__()

    def start(self):
        super(CAGRAnalyzer, self).start()


        # 获取初始值（可以是策略的资产值或者基金值）

        self._value_start = self.strategy.broker.getvalue()

        
        # 初始化累计收益率的初始值
        self._cum_return = 1.0  # 用1.0来初始化，以便于累乘

        # 用于存储收益率的时间步
        self._returns = []

    def stop(self):
        # 计算CAGR和夏普比率
        annual_factor = self._TANN.get(self.p.period, 252.0)
        
        # 计算总年数
        num_years = len(self._returns) / annual_factor  # 数据长度除以年化因子
        
        # 计算年化复合增长率（CAGR）
        if num_years > 0:
            cagr = (self._cum_return) ** (1 / num_years) - 1
        else:
            cagr = 0.0  # 如果没有数据，设置为0
        #计算sharp self.p.riskfreerate
        mean_return = np.mean(self._returns) * annual_factor
        var_return = np.std(self._returns) * np.sqrt(annual_factor)
        sharpe = mean_return/var_return
        # 存储结果
        self.rets['cagr'] = cagr
        self.rets['sharpe'] = sharpe
        
        # 如果plot参数为True，则绘制累积收益率图表
        if self.p.plot and len(self.dates) > 0:
            self.plot_cumulative_returns()

    def next(self):
        '''Calculate returns on each time step'''
        # 计算每个时间步骤的收益率

        # if self._value_start != 0.0:


        # current_value = self.strategy.broker.getvalue() if not self._fundmode else self.strategy.broker.fundvalue
        current_value = self.strategy.broker.getvalue()
        

        #分子分母为0
        daily_return =0 if self._value_start == 0 else  (current_value / self._value_start) - 1
        daily_return = 0 if daily_return == -1 else daily_return

        self._returns.append(daily_return)  # 将当前时间的收益率存储起来

        # 累乘每日收益率
        self._cum_return *= (1 + daily_return)
        
        # 记录日期和累积收益率
        self.dates.append(self.strategy.datetime.date())
        self.cum_returns.append(self._cum_return)
        
        # print(self._cum_return,daily_return,self.strategy.broker._valuemkt,self.strategy.broker.getvalue(),self.strategy.broker.getcash())


        # 更新初始值（当新的时间段（天、周、月等）开始时，使用当前值作为新的初始值）
        # self._value_start = self.strategy.broker.getvalue() if not self._fundmode else self.strategy.broker.fundvalue
        self._value_start = self.strategy.broker.getvalue()

    def plot_cumulative_returns(self):
        '''绘制累积收益率图表'''
        plt.figure(figsize=(10, 6))
        plt.plot(self.dates, self.cum_returns, 'b-', linewidth=2)
        plt.title('cumulative returns')
        plt.xlabel('date')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def get_analysis(self):
        '''Returns the CAGR value'''

        return self.rets