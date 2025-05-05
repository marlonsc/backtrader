import backtrader as bt
import pandas as pd
import numpy as np
import sys
import os
import datetime

from arbitrage.myutil import calculate_spread, check_and_align_data, cointegration_ratio
# https://mp.weixin.qq.com/s/na-5duJiRM1fTJF0WrcptA


def calculate_rolling_spread(df0, df1, window: int = 90):
    """滚动计算 β 和价差（spread）"""
    # 1. 对齐并合并价格
    df = (df0.set_index('date')['close']
               .rename('close0')
               .to_frame()
               .join(df1.set_index('date')['close']
                         .rename('close1'),
                     how='inner'))

    # 2. 计算滚动 β（向量化做法，比 rolling-apply 快很多）
    cov  = df['close0'].rolling(window).cov(df['close1'])
    var1 = df['close1'].rolling(window).var()
    beta = (cov / var1).round(1)

    # 3. 计算价差
    spread = df['close0'] - beta * df['close1']

    # 4. 整理输出
    out = (pd.DataFrame({'date': df.index,
                         'beta': beta,
                         'close': spread})
             .dropna()
             .reset_index(drop=True))
    
    # 5. 确保日期列是正确的日期类型
    out['date'] = pd.to_datetime(out['date'])
    
    return out

# 读取数据
output_file = 'D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5'
df0 = pd.read_hdf(output_file, key='/J').reset_index()
df1 = pd.read_hdf(output_file, key='/JM').reset_index()

# 确保日期列格式正确
df0['date'] = pd.to_datetime(df0['date'])
df1['date'] = pd.to_datetime(df1['date'])

# 计算滚动价差
df_spread = calculate_rolling_spread(df0, df1, window=60)
print("滚动价差计算完成，系数示例：")
print(df_spread.head())

fromdate = datetime.datetime(2018, 1, 1)
todate = datetime.datetime(2025, 1, 1)

# 创建自定义数据类以支持beta列
class SpreadData(bt.feeds.PandasData):
    lines = ('beta',)  # 添加beta线
    
    params = (
        ('datetime', 'date'),  # 日期列
        ('close', 'close'),    # 价差列作为close
        ('beta', 'beta'),      # beta列
        ('nocase', True),      # 列名不区分大小写
    )

# 添加数据
data0 = bt.feeds.PandasData(dataname=df0, datetime='date', nocase=True, fromdate=fromdate, todate=todate)
data1 = bt.feeds.PandasData(dataname=df1, datetime='date', nocase=True, fromdate=fromdate, todate=todate)
data2 = SpreadData(dataname=df_spread, fromdate=fromdate, todate=todate)

class DynamicSpreadStrategy(bt.Strategy):
    params = (
        ('period', 30),
        ('devfactor', 2),
    )

    def __init__(self):
        # 布林带指标 - 使用传入的价差数据
        self.boll = bt.indicators.BollingerBands(
            self.data2.close,
            period=self.p.period,
            devfactor=self.p.devfactor,
            subplot=False
        )

        # 交易状态
        self.order = None
        self.entry_price = 0

    def next(self):
        if self.order:
            return

        # 获取当前beta值
        current_beta = self.data2.beta[0]
        
        # 处理缺失beta情况
        if pd.isna(current_beta) or current_beta <= 0:
            return
            
        # 动态设置交易规模
        self.size0 = 10  # 固定J的规模
        self.size1 = round(current_beta * 10)  # 根据beta调整JM的规模
        
        # 打印调试信息
        if len(self) % 20 == 0:  # 每20个bar打印一次，减少输出
            print(f'{self.datetime.date()}: beta={current_beta}, J:{self.size0}手, JM:{self.size1}手')

        # 使用传入的价差数据
        spread = self.data2.close[0]
        mid = self.boll.lines.mid[0]
        pos = self.getposition(self.data0).size

        # 开平仓逻辑
        if pos == 0:
            if spread > self.boll.lines.top[0]:
                self._open_position(short=True)
            elif spread < self.boll.lines.bot[0]:
                self._open_position(short=False)
        else:
            if (spread <= mid and pos < 0) or (spread >= mid and pos > 0):
                self._close_positions()

    def _open_position(self, short):
        '''动态配比下单'''
        # 确认交易规模有效
        if not hasattr(self, 'size0') or not hasattr(self, 'size1'):
            self.size0 = 10  # 默认值
            self.size1 = round(self.data2.beta[0] * 10) if not pd.isna(self.data2.beta[0]) else 14
        
        if short:
            print(f'做空J {self.size0}手, 做多JM {self.size1}手')
            self.sell(data=self.data0, size=self.size0)
            self.buy(data=self.data1, size=self.size1)
        else:
            print(f'做多J {self.size0}手, 做空JM {self.size1}手')
            self.buy(data=self.data0, size=self.size0)
            self.sell(data=self.data1, size=self.size1)
        self.entry_price = self.data2.close[0]

    def _close_positions(self):
        self.close(data=self.data0)
        self.close(data=self.data1)

    def notify_trade(self, trade):
        if trade.isclosed:
            print('TRADE %s CLOSED %s, PROFIT: GROSS %.2f, NET %.2f, PRICE %d' %
                  (trade.ref, bt.num2date(trade.dtclose), trade.pnl, trade.pnlcomm, trade.value))
        elif trade.justopened:
            print('TRADE %s OPENED %s  , SIZE %2d, PRICE %d ' % (
            trade.ref, bt.num2date(trade.dtopen), trade.size, trade.value))

    # def notify_order(self, order):
    #     if order.status in [order.Submitted, order.Accepted]:
    #         # 订单状态 submitted/accepted，处于未决订单状态。
    #         return
    #
    #     # 订单已决，执行如下语句
    #     if order.status in [order.Completed]:
    #         if order.isbuy():
    #             print(f'executed date {bt.num2date(order.executed.dt)},executed price {order.executed.price}, created date {bt.num2date(order.created.dt)}')


# 创建回测引擎
cerebro = bt.Cerebro(stdstats=False)
cerebro.adddata(data0, name='data0')
cerebro.adddata(data1, name='data1')
cerebro.adddata(data2, name='spread')

# cerebro.broker.setcommission(
#     commission=0.001,  # 0.1% 费率
#     margin=False,       # 非保证金交易
#     mult=1,            # 价格乘数
# )
# # # 百分比滑点
# cerebro.broker.set_slippage_perc(
#     perc=0.0005,        # 0.5% 滑点
#     slip_open=True,    # 影响开盘价
#     slip_limit=True,   # 影响限价单
#     slip_match=True,   # 调整成交价
#     slip_out=True      # 允许滑出价格范围
# )


# 添加策略
cerebro.addstrategy(DynamicSpreadStrategy)
##########################################################################################
# 设置初始资金
cerebro.broker.setcash(100000)
cerebro.broker.set_shortcash(False)
cerebro.addanalyzer(bt.analyzers.DrawDown)  # 回撤分析器
cerebro.addanalyzer(bt.analyzers.ROIAnalyzer, period=bt.TimeFrame.Days)
cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                    timeframe=bt.TimeFrame.Days,  # 按日数据计算
                    riskfreerate=0,            # 默认年化1%的风险无风险利率
                    annualize=True,           # 不进行年化
                    )
cerebro.addanalyzer(bt.analyzers.Returns,
                    tann=bt.TimeFrame.Days,  # 年化因子，252 个交易日
                    )
cerebro.addanalyzer(bt.analyzers.CAGRAnalyzer, period=bt.TimeFrame.Days)  # 这里的period可以是daily, weekly, monthly等
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

# cerebro.addobserver(bt.observers.CashValue)
# cerebro.addobserver(bt.observers.Value)

cerebro.addobserver(bt.observers.Trades)
# cerebro.addobserver(bt.observers.BuySell)
cerebro.addobserver(bt.observers.CumValue)

# 运行回测
results = cerebro.run()
#
# 获取分析结果
drawdown = results[0].analyzers.drawdown.get_analysis()
sharpe = results[0].analyzers.sharperatio.get_analysis()
roi = results[0].analyzers.roianalyzer.get_analysis()
total_returns = results[0].analyzers.returns.get_analysis()  # 获取总回报率
cagr = results[0].analyzers.cagranalyzer.get_analysis()
# trade_analysis = results[0].analyzers.tradeanalyzer.get_analysis()  # 通过名称获取分析结果

# # 打印分析结果
print("=============回测结果================")
print(f"\nSharpe Ratio: {sharpe['sharperatio']:.2f}")
print(f"Drawdown: {drawdown['max']['drawdown']:.2f} %")
print(f"Annualized/Normalized return: {total_returns['rnorm100']:.2f}%")  #
print(f"Total compound return: {roi['roi100']:.2f}%")
print(f"年化收益: {cagr['cagr']:.2f} ")
print(f"夏普比率: {cagr['sharpe']:.2f}")
# 绘制结果
cerebro.plot(volume=False, spread=True)

