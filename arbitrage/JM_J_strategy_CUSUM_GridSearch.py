import backtrader as bt
import pandas as pd
import numpy as np
import sys
import os
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import argparse

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

class DynamicSpreadCUSUMStrategy(bt.Strategy):
    params = (
        ('win', 20),          # rolling 窗口
        ('k_coeff', 0.5),     # κ = k_coeff * σ
        ('h_coeff', 5.0),     # h = h_coeff * σ
        ('base_holding_days', 3),  # 基础持仓天数
        ('days_factor', 2.0),  # 持仓天数动态调整因子
        ('verbose', False),   # 是否打印详细信息
    )

    def __init__(self):
        # 保存两条累积和
        self.g_pos, self.g_neg = 0.0, 0.0          # CUSUM state
        # 方便读取最近 win 根价差
        self.spread_series = self.data2.close

        ########### 新增：初始化存储滚动均值的数组 ###########
        self.rolling_mu = bt.ind.SMA(self.data2.close, period=self.p.win)  # 滚动均值
        
        # 新增：持仓天数计数器
        self.holding_counter = 0
        self.target_holding_days = 0  # 目标持仓天数，会动态计算
        self.in_position = False
        
        # 统计变量
        self.total_trades = 0
        self.total_holding_days = 0
        self.holding_days_list = []  # 记录每笔交易的持仓天数
        self.trade_start_date = None

    # ---------- 交易辅助（沿用原有逻辑） ----------
    def _open_position(self, short, signal_strength):
        if not hasattr(self, 'size0'):
            self.size0 = 10
            self.size1 = round(self.data2.beta[0] * 10)
        if short:                                 # 做空价差
            self.sell(data=self.data0, size=self.size0)
            self.buy (data=self.data1, size=self.size1)
        else:                                     # 做多价差
            self.buy (data=self.data0, size=self.size0)
            self.sell(data=self.data1, size=self.size1)
        
        # 动态计算目标持仓天数，基于信号强度
        # 信号越强，持仓天数越长
        dynamic_days = int(self.p.days_factor * signal_strength)
        self.target_holding_days = max(self.p.base_holding_days, self.p.base_holding_days + dynamic_days)
        
        if self.p.verbose:
            print(f"信号强度: {signal_strength:.2f}, 目标持仓天数: {self.target_holding_days}")
        
        # 重置持仓计数器
        self.holding_counter = 0
        self.in_position = True
        self.total_trades += 1
        self.trade_start_date = self.datetime.date()

    def _close_positions(self):
        self.close(data=self.data0)
        self.close(data=self.data1)
        self.in_position = False
        
        # 更新统计数据
        self.total_holding_days += self.holding_counter
        self.holding_days_list.append(self.holding_counter)
        
        if self.p.verbose:
            print(f"交易持仓时间: {self.holding_counter}天, "
                  f"从 {self.trade_start_date} 到 {self.datetime.date()}")

    def next(self):
    # ---------- 主循环 ----------
        ########### 修改：计算动态均值 μ ###########
        # 取前 win 根价差（不含当根）
        hist = self.spread_series.get(size=self.p.win, ago=0)  
        mu = np.mean(hist)  
        sigma = np.std(hist, ddof=1)
        
        if np.isnan(sigma) or sigma == 0:
            return
        
        kappa = self.p.k_coeff * sigma
        h     = self.p.h_coeff * sigma

        s_t   = self.spread_series[0]
        
        ########### 关键修改：使用修正后的价差 ###########
        s_t_corrected = s_t - mu  # 修正价差
        
        # 3) 更新正/负累积和（使用修正价差）
        self.g_pos = max(0, self.g_pos + s_t_corrected - kappa)  ###########
        self.g_neg = max(0, self.g_neg - s_t_corrected - kappa)  ###########
        
        position_size = self.getposition(self.data0).size

        # 4) 开仓逻辑（保持不变）
        if position_size == 0:
            beta_now = self.data2.beta[0]
            if pd.isna(beta_now) or beta_now <= 0:
                return
            self.size0 = 10
            self.size1 = round(beta_now * 10)
            
            if self.g_pos > h:
                # 计算信号强度：累积和超过阈值h的幅度
                signal_strength = (self.g_pos - h) / h               
                self._open_position(short=True, signal_strength=signal_strength)
                self.g_pos = self.g_neg = 0       
            elif self.g_neg > h:
                # 计算信号强度：累积和超过阈值h的幅度
                signal_strength = (self.g_neg - h) / h
                self._open_position(short=False, signal_strength=signal_strength)
                self.g_pos = self.g_neg = 0
        else:
            # 已有持仓：增加持仓天数计数
            if self.in_position:
                self.holding_counter += 1
                
                # 当持仓达到目标持仓天数时平仓
                if self.holding_counter >= self.target_holding_days:
                    if self.p.verbose:
                        print(f"持仓达到目标天数{self.target_holding_days}天，平仓")
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

    def get_stats(self):
        """返回策略统计数据"""
        stats = {
            'total_trades': self.total_trades,
            'total_holding_days': self.total_holding_days,
            'avg_holding_days': self.total_holding_days / max(1, self.total_trades),
            'holding_days_list': self.holding_days_list,
            'max_holding_days': max(self.holding_days_list) if self.holding_days_list else 0,
            'min_holding_days': min(self.holding_days_list) if self.holding_days_list else 0,
        }
        return stats

def run_strategy(data0, data1, data2, win, k_coeff, h_coeff, base_holding_days, days_factor, spread_window=60, initial_cash=100000):
    """运行单次回测"""
    # 创建回测引擎
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(data0, name='data0')
    cerebro.adddata(data1, name='data1')
    cerebro.adddata(data2, name='spread')

    # 添加策略
    cerebro.addstrategy(DynamicSpreadCUSUMStrategy,
                        win=win,
                        k_coeff=k_coeff,
                        h_coeff=h_coeff,
                        base_holding_days=base_holding_days,  # 基础持仓天数
                        days_factor=days_factor,  # 天数调整因子
                        verbose=False)

    # 设置初始资金
    cerebro.broker.setcash(initial_cash)
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
    
    # 获取策略自定义统计
    strategy_stats = strat.get_stats()
    
    return {
        'sharpe': sharpe,
        'drawdown': drawdown,
        'returns': returns,
        'roi': roi,
        'total_trades': total_trades,
        'win_trades': win_trades,
        'loss_trades': loss_trades,
        'win_rate': win_rate,
        'avg_holding_days': strategy_stats['avg_holding_days'],
        'max_holding_days': strategy_stats['max_holding_days'],
        'min_holding_days': strategy_stats['min_holding_days'],
        'params': {
            'win': win,
            'k_coeff': k_coeff,
            'h_coeff': h_coeff,
            'base_holding_days': base_holding_days,
            'days_factor': days_factor,
            'spread_window': spread_window
        }
    }

def grid_search(pair1=None, pair2=None, initial_cash=100000, 
                win_values=None, k_coeff_values=None, h_coeff_values=None, 
                base_holding_days_values=None, days_factor_values=None, 
                spread_windows=None):
    """执行网格搜索找到最优参数"""
    # 读取数据
    output_file = '/Users/f/Desktop/ricequant/1d_2017to2024_noadjust.h5'
    
    # 使用默认对 '/J' 和 '/JM' 如果未指定
    pair1 = pair1 or '/J' 
    pair2 = pair2 or '/JM'
    
    df0 = pd.read_hdf(output_file, key=pair1).reset_index()
    df1 = pd.read_hdf(output_file, key=pair2).reset_index()

    # 确保日期列格式正确
    df0['date'] = pd.to_datetime(df0['date'])
    df1['date'] = pd.to_datetime(df1['date'])

    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)

    # 使用默认参数网格（如果未指定）
    if win_values is None:
        win_values = [7, 14]
        
    if k_coeff_values is None:
        k_coeff_values = [0.2, 0.5, 0.8, 1.0]
        
    if h_coeff_values is None:
        h_coeff_values = [4.0, 8.0, 12.0]
        
    if base_holding_days_values is None:
        base_holding_days_values = [3,5]
        
    if days_factor_values is None:
        days_factor_values = [1, 3, 5, 7]
        
    if spread_windows is None:
        spread_windows = [15, 30]
        
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
        
        for win in win_values:
            for k_coeff in k_coeff_values:
                for h_coeff in h_coeff_values:
                    for base_holding_days in base_holding_days_values:
                        for days_factor in days_factor_values:
                            param_combinations.append((data0, data1, data2, win, k_coeff, h_coeff, 
                                                      base_holding_days, days_factor, spread_window))
    
    # 执行网格搜索
    results = []
    total_combinations = len(param_combinations)
    
    print(f"开始网格搜索，共{total_combinations}种参数组合...")
    
    for i, (data0, data1, data2, win, k_coeff, h_coeff, base_holding_days, days_factor, spread_window) in enumerate(param_combinations):
        print(f"测试参数组合 {i+1}/{total_combinations}: win={win}, k_coeff={k_coeff:.1f}, "
              f"h_coeff={h_coeff:.1f}, base_days={base_holding_days}, factor={days_factor:.1f}, spread_window={spread_window}")
        
        # try:
        result = run_strategy(data0, data1, data2, win, k_coeff, h_coeff, base_holding_days, 
                             days_factor, spread_window, initial_cash)
        results.append(result)
        
        # 打印当前结果
        print(f"  夏普比率: {result['sharpe']:.4f}, 最大回撤: {result['drawdown']:.2f}%, 年化收益: {result['returns']:.2f}%, 胜率: {result['win_rate']:.2f}%")
        print(f"  交易次数: {result['total_trades']}, 平均持仓天数: {result['avg_holding_days']:.2f}天 (最短: {result['min_holding_days']}天, 最长: {result['max_holding_days']}天)")
        
        # except Exception as e:
        #     print(f"  参数组合出错: {e}")
    
    # 找出最佳参数组合
    if results:
        # 按夏普比率排序
        sorted_results = sorted(results, key=lambda x: x['sharpe'] if x['sharpe'] is not None else -float('inf'), reverse=True)
        best_result = sorted_results[0]
        
        print("\n========= 最佳参数组合 =========")
        print(f"对子: {pair1}/{pair2}")
        print(f"价差计算窗口: {best_result['params']['spread_window']}")
        print(f"Rolling窗口 (win): {best_result['params']['win']}")
        print(f"κ系数 (k_coeff): {best_result['params']['k_coeff']:.2f}")
        print(f"h系数 (h_coeff): {best_result['params']['h_coeff']:.2f}")
        print(f"基础持仓天数: {best_result['params']['base_holding_days']}")
        print(f"天数调整因子: {best_result['params']['days_factor']:.2f}")
        print(f"夏普比率: {best_result['sharpe']:.4f}")
        print(f"最大回撤: {best_result['drawdown']:.2f}%")
        print(f"年化收益: {best_result['returns']:.2f}%")
        print(f"总收益率: {best_result['roi']:.2f}%")
        print(f"总交易次数: {best_result['total_trades']}")
        print(f"胜率: {best_result['win_rate']:.2f}%")
        print(f"平均持仓天数: {best_result['avg_holding_days']:.2f}天")
        print(f"持仓天数范围: {best_result['min_holding_days']}至{best_result['max_holding_days']}天")
        

        # 显示所有结果，按夏普比率排序
        print("\n========= 所有参数组合结果（按夏普比率排序）=========")
        for i, result in enumerate(sorted_results[:10]):  # 只显示前10个最好的结果
            print(f"{i+1}. spread_window={result['params']['spread_window']}, "
                  f"win={result['params']['win']}, "
                  f"k_coeff={result['params']['k_coeff']:.2f}, "
                  f"h_coeff={result['params']['h_coeff']:.2f}, "
                  f"base_days={result['params']['base_holding_days']}, "
                  f"factor={result['params']['days_factor']:.2f}, "
                  f"sharpe={result['sharpe']:.4f}, "
                  f"drawdown={result['drawdown']:.2f}%, "
                  f"return={result['returns']:.2f}%, "
                  f"win_rate={result['win_rate']:.2f}%, "
                  f"trades={result['total_trades']}, "
                  f"avg_days={result['avg_holding_days']:.1f}")
    else:
        print("未找到有效的参数组合")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='动态CUSUM策略参数网格搜索')
    
    # 合约对参数
    parser.add_argument('--pair1', type=str, default='/J', help='第一个合约代码 (默认: /J)')
    parser.add_argument('--pair2', type=str, default='/JM', help='第二个合约代码 (默认: /JM)')
    
    # 初始资金
    parser.add_argument('--cash', type=int, default=100000, help='初始资金 (默认: 100000)')
    
    # 策略参数
    parser.add_argument('--win', nargs='+', type=int, default=[7, 14], 
                        help='Rolling窗口值列表 (默认: 7 14)')
    parser.add_argument('--k-coeff', nargs='+', type=float, default=[0.2, 0.5, 0.8, 1.0], 
                        help='κ系数值列表 (默认: 0.2 0.5 0.8 1.0)')
    parser.add_argument('--h-coeff', nargs='+', type=float, default=[4, 8.0, 12.0], 
                        help='h系数值列表 (默认: 4 8.0 12.0)')
    parser.add_argument('--base-days', nargs='+', type=int, default=[1], 
                        help='基础持仓天数列表 (默认: 1)')
    parser.add_argument('--days-factor', nargs='+', type=float, default=[1, 3, 5, 7], 
                        help='天数调整因子列表 (默认: 1 3 5 7)')
    parser.add_argument('--spread-windows', nargs='+', type=int, default=[15, 30], 
                        help='价差计算窗口列表 (默认: 15 30)')
    
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    grid_search(
        pair1=args.pair1,
        pair2=args.pair2,
        initial_cash=args.cash,
        win_values=args.win,
        k_coeff_values=args.k_coeff,
        h_coeff_values=args.h_coeff,
        base_holding_days_values=args.base_days,
        days_factor_values=args.days_factor,
        spread_windows=args.spread_windows
    ) 




# ========= 最佳参数组合 =========
# 价差计算窗口: 15
# Rolling窗口 (win): 14
# κ系数 (k_coeff): 0.50
# h系数 (h_coeff): 4.00
# 基础持仓天数: 5
# 天数调整因子: 5.00
# 夏普比率: 0.5480
# 最大回撤: 9.04%
# 年化收益: 2.53%
# 总收益率: 2.53%
# 总交易次数: 340
# 胜率: 49.71%
# 平均持仓天数: 6.13天
# 持仓天数范围: 5至25天

# ========= 所有参数组合结果（按夏普比率排序）=========
# 1. spread_window=15, win=14, k_coeff=0.50, h_coeff=4.00, base_days=5, factor=5.00, sharpe=0.5480, drawdown=9.04%, return=2.53%, win_rate=49.71%, trades=340, avg_days=6.1
# 2. spread_window=30, win=7, k_coeff=0.80, h_coeff=8.00, base_days=5, factor=3.00, sharpe=0.4927, drawdown=5.67%, return=1.83%, win_rate=51.37%, trades=146, avg_days=5.7
# 3. spread_window=15, win=7, k_coeff=0.50, h_coeff=8.00, base_days=5, factor=1.00, sharpe=0.4886, drawdown=6.48%, return=1.90%, win_rate=51.01%, trades=198, avg_days=5.2
# 4. spread_window=15, win=7, k_coeff=1.00, h_coeff=8.00, base_days=3, factor=1.00, sharpe=0.4716, drawdown=0.65%, return=0.29%, win_rate=57.14%, trades=28, avg_days=3.0
# 5. spread_window=30, win=14, k_coeff=0.80, h_coeff=4.00, base_days=3, factor=3.00, sharpe=0.4713, drawdown=6.41%, return=1.50%, win_rate=52.58%, trades=310, avg_days=3.1
# 6. spread_window=30, win=7, k_coeff=0.50, h_coeff=12.00, base_days=5, factor=3.00, sharpe=0.4692, drawdown=5.93%, return=1.80%, win_rate=49.46%, trades=186, avg_days=6.0
# 7. spread_window=30, win=14, k_coeff=0.80, h_coeff=4.00, base_days=3, factor=1.00, sharpe=0.4631, drawdown=7.47%, return=1.49%, win_rate=51.27%, trades=314, avg_days=3.0
# 8. spread_window=30, win=14, k_coeff=0.20, h_coeff=4.00, base_days=5, factor=5.00, sharpe=0.4602, drawdown=10.94%, return=2.59%, win_rate=45.45%, trades=198, avg_days=17.1
# 9. spread_window=30, win=7, k_coeff=0.50, h_coeff=12.00, base_days=5, factor=1.00, sharpe=0.4600, drawdown=5.11%, return=1.73%, win_rate=49.46%, trades=186, avg_days=5.2
# 10. spread_window=30, win=7, k_coeff=0.50, h_coeff=12.00, base_days=5, factor=5.00, sharpe=0.4518, drawdown=7.10%, return=1.82%, win_rate=47.80%, trades=182, avg_days=7.0