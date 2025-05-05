import backtrader as bt
import pandas as pd
import numpy as np
import sys
import os
import datetime
import matplotlib.pyplot as plt
import seaborn as sns

from arbitrage.myutil import calculate_spread, check_and_align_data, cointegration_ratio

def calculate_rolling_spread(
        df0: pd.DataFrame,          # 必含 'date' 与价格列
        df1: pd.DataFrame,
        window: int = 30,
        fields=('open', 'high', 'low', 'close')
    ) -> pd.DataFrame:
    """
    计算滚动 β，并为指定价格字段生成价差 (spread)：
        spread_x = price0_x - β_{t-1} * price1_x
    """
    # 1) 用收盘价对齐合并（β 仍用 close 估计）
    df = (df0.set_index('date')[['close']]
              .rename(columns={'close': 'close0'})
              .join(df1.set_index('date')[['close']]
                        .rename(columns={'close': 'close1'}),
                    how='inner'))

    # 2) 估计 β_t ，再向前挪一天
    beta_raw   = df['close0'].rolling(window).cov(df['close1']) / \
                 df['close1'].rolling(window).var()
    beta_shift = beta_raw.shift(1).round(1)        # 防未来 + 保留 1 位小数

    # 3) 把 β 拼回主表（便于后面 vectorized 计算）
    df = df.assign(beta=beta_shift)

    # 4) 对每个字段算 spread
    out_cols = {'date': df.index, 'beta': beta_shift}
    for f in fields:
        if f not in ('open','high','low','close'):
            raise ValueError(f'未知字段 {f}')
        p0 = df0.set_index('date')[f]
        p1 = df1.set_index('date')[f]
        aligned = p0.to_frame(name=f'price0_{f}').join(
                  p1.to_frame(name=f'price1_{f}'), how='inner')
        spread_f = aligned[f'price0_{f}'] - beta_shift * aligned[f'price1_{f}']
        out_cols[f'{f}'] = spread_f

    # 5) 整理输出
    out = (pd.DataFrame(out_cols)
             .dropna()
             .reset_index(drop=True))
    out['date'] = pd.to_datetime(out['date'])
    return out

# 创建自定义数据类以支持beta列
class SpreadData(bt.feeds.PandasData):
    lines = ('beta',)  # 添加beta线
    
    params = (
        ('datetime', 'date'),  # 日期列
        ('close', 'close'),    # 价差列作为close
        ('beta', 'beta'),      # beta列
        ('nocase', True),      # 列名不区分大小写
    )

class DynamicSpreadRSIBollingerStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),    # RSI计算窗口
        ('rsi_upper', 70),     # RSI上边界
        ('rsi_lower', 30),     # RSI下边界
        ('bb_period', 20),     # 布林带周期
        ('bb_devfactor', 2.0), # 布林带标准差倍数
        ('verbose', False),    # 是否打印详细信息
    )

    def __init__(self):
        # 方便读取价差
        self.spread_series = self.data2.close
        
        # 计算价差的RSI
        self.rsi = bt.indicators.RSI(self.spread_series, period=self.p.rsi_period)
        
        # 计算价差的布林带
        self.bbands = bt.indicators.BollingerBands(
            self.spread_series, 
            period=self.p.bb_period,
            devfactor=self.p.bb_devfactor
        )
        
        # 布林带各轨道
        self.bb_mid = self.bbands.mid
        self.bb_top = self.bbands.top
        self.bb_bot = self.bbands.bot
        
        # 价格与各轨道的百分比位置 (0-100)
        self.bb_pct = bt.indicators.BollingerBandsPct(
            self.spread_series,
            period=self.p.bb_period,
            devfactor=self.p.bb_devfactor
        )

    def _open_position(self, short):
        if not hasattr(self, 'size0'):
            self.size0 = 10
            self.size1 = round(self.data2.beta[0] * 10)
        if short:                                 # 做空价差
            self.sell(data=self.data0, size=self.size0)
            self.buy (data=self.data1, size=self.size1)
        else:                                     # 做多价差
            self.buy (data=self.data0, size=self.size0)
            self.sell(data=self.data1, size=self.size1)

    def _close_positions(self):
        self.close(data=self.data0)
        self.close(data=self.data1)

    def next(self):
        # 确保有足够的历史数据
        if len(self.rsi) < self.p.rsi_period + 2 or len(self.bbands) < self.p.bb_period + 2:
            return

        # 获取当前指标值
        rsi_value = self.rsi[0]
        bb_pct_value = self.bb_pct[0] * 100  # 转为0-100的百分比
        
        # 当前价格
        price = self.spread_series[0]
        
        position_size = self.getposition(self.data0).size

        # 交易逻辑
        if position_size == 0:  # 当前无持仓
            # 计算动态配比
            beta_now = self.data2.beta[0]
            if pd.isna(beta_now) or beta_now <= 0:
                return
            self.size0 = 10
            self.size1 = round(beta_now * 10)

            # 入场条件: RSI超买/超卖 + 价格突破布林带
            if rsi_value > self.p.rsi_upper and price > self.bb_top[0]:  
                # RSI超买 + 价格突破上轨 → 做空价差
                self._open_position(short=True)
            elif rsi_value < self.p.rsi_lower and price < self.bb_bot[0]:  
                # RSI超卖 + 价格突破下轨 → 做多价差
                self._open_position(short=False)
        else:  # 当前有持仓，考虑平仓
            # 出场条件: 价格回归中轨
            
            if position_size > 0 and price >= self.bb_mid[0]:  
                # 做多价差，当价格上穿或到达中轨 → 平仓
                self._close_positions()
            elif position_size < 0 and price <= self.bb_mid[0]:  
                # 做空价差，当价格下穿或到达中轨 → 平仓
                self._close_positions()

    def notify_trade(self, trade):
        if not self.p.verbose:
            return
            
        if trade.isclosed:
            print('TRADE %s CLOSED %s, PROFIT: GROSS %.2f, NET %.2f, PRICE %d' %
                  (trade.ref, bt.num2date(trade.dtclose), trade.pnl, trade.pnlcomm, trade.value))
        elif trade.justopened:
            print('TRADE %s OPENED %s  , SIZE %2d, PRICE %d ' % (
            trade.ref, bt.num2date(trade.dtopen), trade.size, trade.value))

def run_strategy(data0, data1, data2, rsi_period, rsi_upper, rsi_lower, bb_period, bb_devfactor, spread_window=60):
    """运行单次回测"""
    # 创建回测引擎
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(data0, name='data0')
    cerebro.adddata(data1, name='data1')
    cerebro.adddata(data2, name='spread')

    # 添加策略
    cerebro.addstrategy(DynamicSpreadRSIBollingerStrategy,
                        rsi_period=rsi_period,
                        rsi_upper=rsi_upper,
                        rsi_lower=rsi_lower,
                        bb_period=bb_period,
                        bb_devfactor=bb_devfactor,
                        verbose=False)

    # 设置初始资金
    cerebro.broker.setcash(100000)
    cerebro.broker.set_shortcash(False)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                        timeframe=bt.TimeFrame.Days,
                        riskfreerate=0,
                        annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.Returns)
    cerebro.addanalyzer(bt.analyzers.ROIAnalyzer, period=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

    # 运行回测
    results = cerebro.run()
    
    # 获取分析结果
    strat = results[0]
    sharpe = strat.analyzers.sharperatio.get_analysis().get('sharperatio', 0)
    drawdown = strat.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', 0)
    returns = strat.analyzers.returns.get_analysis().get('rnorm100', 0)
    roi = strat.analyzers.roianalyzer.get_analysis().get('roi100', 0)
    trades = strat.analyzers.tradeanalyzer.get_analysis()
    
    # 获取交易统计
    total_trades = trades.get('total', {}).get('total', 0)
    win_trades = trades.get('won', {}).get('total', 0)
    loss_trades = trades.get('lost', {}).get('total', 0)
    win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0
    
    return {
        'sharpe': sharpe,
        'drawdown': drawdown,
        'returns': returns,
        'roi': roi,
        'total_trades': total_trades,
        'win_trades': win_trades,
        'loss_trades': loss_trades,
        'win_rate': win_rate,
        'params': {
            'rsi_period': rsi_period,
            'rsi_upper': rsi_upper,
            'rsi_lower': rsi_lower,
            'bb_period': bb_period,
            'bb_devfactor': bb_devfactor,
            'spread_window': spread_window
        }
    }

def grid_search():
    """执行网格搜索找到最优参数"""
    # 读取数据
    output_file = '/Users/f/Desktop/ricequant/1d_2017to2024_noadjust.h5'
    df0 = pd.read_hdf(output_file, key='/J').reset_index()
    df1 = pd.read_hdf(output_file, key='/JM').reset_index()

    # 确保日期列格式正确
    df0['date'] = pd.to_datetime(df0['date'])
    df1['date'] = pd.to_datetime(df1['date'])

    fromdate = datetime.datetime(2018, 1, 1)
    todate = datetime.datetime(2025, 1, 1)

    # 定义参数网格
    rsi_period_values = [7, 14, 21]             # RSI计算窗口
    rsi_upper_values = [ 60]             # RSI上边界
    rsi_lower_values = [40]             # RSI下边界
    bb_period_values = [15, 20, 30]             # 布林带周期
    bb_devfactor_values = [1.5, 2.0, 2.5]       # 布林带标准差倍数
    spread_windows = [20, 30, 60]               # 价差计算窗口
    
    # 生成参数组合
    param_combinations = []
    for spread_window in spread_windows:
        # 计算当前窗口下的滚动价差
        print(f"计算滚动价差 (window={spread_window})...")
        df_spread = calculate_rolling_spread(df0, df1, window=spread_window)
        
        # 添加数据
        data0 = bt.feeds.PandasData(dataname=df0, datetime='date', nocase=True, fromdate=fromdate, todate=todate)
        data1 = bt.feeds.PandasData(dataname=df1, datetime='date', nocase=True, fromdate=fromdate, todate=todate)
        data2 = SpreadData(dataname=df_spread, fromdate=fromdate, todate=todate)
        
        for rsi_period in rsi_period_values:
            for rsi_upper in rsi_upper_values:
                for rsi_lower in rsi_lower_values:
                    for bb_period in bb_period_values:
                        for bb_devfactor in bb_devfactor_values:
                            param_combinations.append((
                                data0, data1, data2, 
                                rsi_period, rsi_upper, rsi_lower, 
                                bb_period, bb_devfactor, 
                                spread_window
                            ))
    
    # 执行网格搜索
    results = []
    total_combinations = len(param_combinations)
    
    print(f"开始网格搜索，共{total_combinations}种参数组合...")
    
    for i, (data0, data1, data2, rsi_period, rsi_upper, rsi_lower, bb_period, bb_devfactor, spread_window) in enumerate(param_combinations):
        print(f"测试参数组合 {i+1}/{total_combinations}: rsi_period={rsi_period}, rsi_upper={rsi_upper}, rsi_lower={rsi_lower}, "
              f"bb_period={bb_period}, bb_devfactor={bb_devfactor}, spread_window={spread_window}")
        
        try:
            result = run_strategy(data0, data1, data2, rsi_period, rsi_upper, rsi_lower, bb_period, bb_devfactor, spread_window)
            results.append(result)
            
            # 打印当前结果
            print(f"  夏普比率: {result['sharpe']:.4f}, 最大回撤: {result['drawdown']:.2f}%, 年化收益: {result['returns']:.2f}%, 胜率: {result['win_rate']:.2f}%")
        except Exception as e:
            print(f"  参数组合出错: {e}")
    
    # 找出最佳参数组合
    if results:
        # 按夏普比率排序
        sorted_results = sorted(results, key=lambda x: x['sharpe'] if x['sharpe'] is not None else -float('inf'), reverse=True)
        best_result = sorted_results[0]
        
        print("\n========= 最佳参数组合 =========")
        print(f"价差计算窗口: {best_result['params']['spread_window']}")
        print(f"RSI周期: {best_result['params']['rsi_period']}")
        print(f"RSI上边界: {best_result['params']['rsi_upper']}")
        print(f"RSI下边界: {best_result['params']['rsi_lower']}")
        print(f"布林带周期: {best_result['params']['bb_period']}")
        print(f"布林带标准差倍数: {best_result['params']['bb_devfactor']}")
        print(f"夏普比率: {best_result['sharpe']:.4f}")
        print(f"最大回撤: {best_result['drawdown']:.2f}%")
        print(f"年化收益: {best_result['returns']:.2f}%")
        print(f"总收益率: {best_result['roi']:.2f}%")
        print(f"总交易次数: {best_result['total_trades']}")
        print(f"胜率: {best_result['win_rate']:.2f}%")
        
        # 显示所有结果，按夏普比率排序
        print("\n========= 所有参数组合结果（按夏普比率排序）=========")
        for i, result in enumerate(sorted_results[:10]):  # 只显示前10个最好的结果
            print(f"{i+1}. spread_window={result['params']['spread_window']}, "
                  f"rsi_period={result['params']['rsi_period']}, "
                  f"rsi_upper={result['params']['rsi_upper']}, "
                  f"rsi_lower={result['params']['rsi_lower']}, "
                  f"bb_period={result['params']['bb_period']}, "
                  f"bb_devfactor={result['params']['bb_devfactor']:.1f}, "
                  f"sharpe={result['sharpe']:.4f}, "
                  f"drawdown={result['drawdown']:.2f}%, "
                  f"return={result['returns']:.2f}%, "
                  f"win_rate={result['win_rate']:.2f}%")
    else:
        print("未找到有效的参数组合")

if __name__ == '__main__':
    grid_search() 