import backtrader as bt
import pandas as pd
import numpy as np
import sys
import os
import datetime
import itertools

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

# 创建分位数指标（自定义）
class QuantileIndicator(bt.Indicator):
    lines = ('upper', 'lower', 'mid')
    params = (
        ('period', 30),
        ('upper_quantile', 0.9),  # 上轨分位数
        ('lower_quantile', 0.1),  # 下轨分位数
    )

    def __init__(self):
        self.addminperiod(self.p.period)
        self.spread_data = []

    def next(self):
        self.spread_data.append(self.data[0])
        if len(self.spread_data) > self.p.period:
            self.spread_data.pop(0)  # 保持固定长度

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
        ('lookback_period', 60),       # 回看周期
        ('upper_quantile', 0.9),       # 上轨分位数
        ('lower_quantile', 0.1),       # 下轨分位数
        ('max_positions', 3),          # 最大加仓次数
        ('add_position_threshold', 0.1),  # 加仓阈值（相对于轨道的百分比）
        ('verbose', True),            # 是否打印详细信息
    )

    def __init__(self):
        # 计算价差的分位数指标
        self.quantile = QuantileIndicator(
            self.data2.close, 
            period=self.p.lookback_period,
            upper_quantile=self.p.upper_quantile,
            lower_quantile=self.p.lower_quantile,
        )
        # 交易状态
        self.order = None
        self.entry_price = 0
        self.entry_direction = None  # 持仓方向：'long'/'short'
        self.position_layers = 0     # 当前持仓层数

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
        if self.p.verbose and len(self) % 20 == 0:  # 每20个bar打印一次，减少输出
            print(f'{self.datetime.date()}: beta={current_beta}, J:{self.size0}手, JM:{self.size1}手')

        # 使用分位数指标进行交易决策
        spread = self.data2.close[0]
        upper_band = self.quantile.upper[0]
        lower_band = self.quantile.lower[0]
        mid_band = self.quantile.mid[0]
        pos = self.getposition(self.data0).size

        # 开平仓逻辑
        if pos == 0:  # 没有持仓
            if spread > upper_band:
                # 价差高于上轨，做空价差（做多J，做空JM）
                self._open_position(short=True)
            elif spread < lower_band:
                # 价差低于下轨，做多价差（做空J，做多JM）
                self._open_position(short=False)
        else:  # 已有持仓
            # 自动加仓逻辑
            if self.position_layers < self.p.max_positions:
                # 多头加仓条件
                if pos > 0:
                    # 以lower_band为基准，spread越低越加仓
                    next_layer = self.position_layers + 1
                    add_threshold = lower_band - next_layer * self.p.add_position_threshold * (upper_band - lower_band)
                    if spread < add_threshold:
                        self._add_position(short=False)
                # 空头加仓条件
                elif pos < 0:
                    # 以upper_band为基准，spread越高越加仓
                    next_layer = self.position_layers + 1
                    add_threshold = upper_band + next_layer * self.p.add_position_threshold * (upper_band - lower_band)
                    if spread > add_threshold:
                        self._add_position(short=True)
            # 平仓逻辑
            if pos > 0 and spread >= mid_band:  # 持有多头且价差回归到中位数
                self._close_positions()
            elif pos < 0 and spread <= mid_band:  # 持有空头且价差回归到中位数
                self._close_positions()

    def _open_position(self, short):
        '''动态配比下单'''
        # 确认交易规模有效
        if not hasattr(self, 'size0') or not hasattr(self, 'size1'):
            self.size0 = 10  # 默认值
            self.size1 = round(self.data2.beta[0] * 10) if not pd.isna(self.data2.beta[0]) else 14
        
        # 检查资金是否足够
        cash = self.broker.getcash()
        cost = self.size0 * self.data0.close[0] + self.size1 * self.data1.close[0]
        if cash < cost:
            if self.p.verbose:
                print(f'资金不足，无法开仓: 需要{cost:.2f}，可用{cash:.2f}')
            return
        
        if short:
            if self.p.verbose:
                print(f'做多J {self.size0}手, 做空JM {self.size1}手')
            self.buy(data=self.data0, size=self.size0)
            self.sell(data=self.data1, size=self.size1)
            self.entry_direction = 'short'
        else:
            if self.p.verbose:
                print(f'做空J {self.size0}手, 做多JM {self.size1}手')
            self.sell(data=self.data0, size=self.size0)
            self.buy(data=self.data1, size=self.size1)
            self.entry_direction = 'long'
        self.entry_price = self.data2.close[0]
        self.position_layers = 1  # 首次开仓为第一层

    def _add_position(self, short):
        '''加仓，自动套利配比，资金检查'''
        # 计算加仓规模（每层同等规模，也可自定义递减）
        add_size0 = self.size0
        add_size1 = self.size1
        # 检查资金
        cash = self.broker.getcash()
        cost = add_size0 * self.data0.close[0] + add_size1 * self.data1.close[0]
        if cash < cost:
            if self.p.verbose:
                print(f'资金不足，无法加仓: 需要{cost:.2f}，可用{cash:.2f}')
            return
        if short:
            # if self.p.verbose:
            print(f'加仓做多J {add_size0}手, 做空JM {add_size1}手')
            self.buy(data=self.data0, size=add_size0)
            self.sell(data=self.data1, size=add_size1)
        else:
            # if self.p.verbose:
            print(f'加仓做空J {add_size0}手, 做多JM {add_size1}手')
            self.sell(data=self.data0, size=add_size0)
            self.buy(data=self.data1, size=add_size1)
        self.position_layers += 1

    def _close_positions(self):
        self.close(data=self.data0)
        self.close(data=self.data1)
        self.position_layers = 0  # 平仓重置加仓层数

    def notify_trade(self, trade):
        if not self.p.verbose:
            return
            
        if trade.isclosed:
            print('TRADE %s CLOSED %s, PROFIT: GROSS %.2f, NET %.2f, PRICE %d' %
                  (trade.ref, bt.num2date(trade.dtclose), trade.pnl, trade.pnlcomm, trade.value))
        elif trade.justopened:
            print('TRADE %s OPENED %s  , SIZE %2d, PRICE %d ' % (
            trade.ref, bt.num2date(trade.dtopen), trade.size, trade.value))


def run_strategy(data0, data1, data2, lookback_period, upper_quantile, lower_quantile, spread_window=60):
    """运行单次回测"""
    # 创建回测引擎
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(data0, name='data0')
    cerebro.adddata(data1, name='data1')
    cerebro.adddata(data2, name='spread')

    # 添加策略
    cerebro.addstrategy(DynamicSpreadQuantileStrategy,
                        lookback_period=lookback_period,
                        upper_quantile=upper_quantile,
                        lower_quantile=lower_quantile,
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
    trades = strat.analyzers.tradeanalyzer.get_analysis().get('total', 0)
    
    return {
        'sharpe': sharpe,
        'drawdown': drawdown,
        'returns': returns,
        'roi': roi,
        'trades': trades,
        'params': {
            'period': lookback_period,
            'upper_quantile': upper_quantile,
            'lower_quantile': lower_quantile,
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
    lookback_periods = [30]
    upper_quantiles = [0.8]
    spread_windows = [ 60]  # 新增：价差计算窗口参数
    
    # 为每个upper_quantile计算对应的lower_quantile
    param_combinations = []
    for spread_window in spread_windows:
        # 计算当前窗口下的滚动价差
        print(f"计算滚动价差 (window={spread_window})...")
        df_spread = calculate_rolling_spread(df0, df1, window=spread_window)
        
        # 添加数据
        data0 = bt.feeds.PandasData(dataname=df0, datetime='date', nocase=True, fromdate=fromdate, todate=todate)
        data1 = bt.feeds.PandasData(dataname=df1, datetime='date', nocase=True, fromdate=fromdate, todate=todate)
        data2 = SpreadData(dataname=df_spread, fromdate=fromdate, todate=todate)
        
        for period in lookback_periods:
            for upper_q in upper_quantiles:
                lower_q = 1 - upper_q  # 对称设置
                param_combinations.append((data0, data1, data2, period, upper_q, lower_q, spread_window))
    
    # 执行网格搜索
    results = []
    total_combinations = len(param_combinations)
    
    print(f"开始网格搜索，共{total_combinations}种参数组合...")
    
    for i, (data0, data1, data2, period, upper_q, lower_q, spread_window) in enumerate(param_combinations):
        print(f"测试参数组合 {i+1}/{total_combinations}: period={period}, upper_q={upper_q:.2f}, lower_q={lower_q:.2f}, spread_window={spread_window}")
        
        try:
            result = run_strategy(data0, data1, data2, period, upper_q, lower_q, spread_window)
            results.append(result)
            
            # 打印当前结果
            print(f"  夏普比率: {result['sharpe']:.4f}, 最大回撤: {result['drawdown']:.2f}%, 年化收益: {result['returns']:.2f}%，交易次数: {result['trades']}")
        except Exception as e:
            print(f"  参数组合出错: {e}")
    
    # 找出最佳参数组合
    if results:
        # 按夏普比率排序
        sorted_results = sorted(results, key=lambda x: x['sharpe'] if x['sharpe'] is not None else -float('inf'), reverse=True)
        best_result = sorted_results[0]
        
        print("\n========= 最佳参数组合 =========")
        print(f"价差计算窗口: {best_result['params']['spread_window']}")
        print(f"回看周期: {best_result['params']['period']}")
        print(f"上轨分位数: {best_result['params']['upper_quantile']:.2f}")
        print(f"下轨分位数: {best_result['params']['lower_quantile']:.2f}")
        print(f"夏普比率: {best_result['sharpe']:.4f}")
        print(f"最大回撤: {best_result['drawdown']:.2f}%")
        print(f"年化收益: {best_result['returns']:.2f}%")
        print(f"总收益率: {best_result['roi']:.2f}%")
        
        # 显示所有结果，按夏普比率排序
        print("\n========= 所有参数组合结果（按夏普比率排序）=========")
        for i, result in enumerate(sorted_results[:10]):  # 只显示前10个最好的结果
            print(f"{i+1}. spread_window={result['params']['spread_window']}, "
                  f"period={result['params']['period']}, "
                  f"upper_q={result['params']['upper_quantile']:.2f}, "
                  f"lower_q={result['params']['lower_quantile']:.2f}, "
                  f"sharpe={result['sharpe']:.4f}, "
                  f"drawdown={result['drawdown']:.2f}%, "
                  f"return={result['returns']:.2f}%")
    else:
        print("未找到有效的参数组合")

# 创建自定义数据类以支持beta列
class SpreadData(bt.feeds.PandasData):
    lines = ('beta',)  # 添加beta线
    
    params = (
        ('datetime', 'date'),  # 日期列
        ('close', 'close'),    # 价差列作为close
        ('beta', 'beta'),      # beta列
        ('nocase', True),      # 列名不区分大小写
    )

if __name__ == '__main__':
    grid_search() 