import backtrader as bt
import pandas as pd
import numpy as np
import sys
import os
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from pathlib import Path

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
        ('verbose', False),   # 是否打印详细信息
    )

    def __init__(self):
        # 保存两条累积和
        self.g_pos, self.g_neg = 0.0, 0.0          # CUSUM state
        # 方便读取最近 win 根价差
        self.spread_series = self.data2.close

    # ---------- 交易辅助（沿用原有逻辑） ----------
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

    # ---------- 主循环 ----------
    def next(self):
        # 1) 确保有足够历史用于 σ 估计
        if len(self.spread_series) < self.p.win + 2:
            return

        # 2) 取"上一 bar"结束时的 rolling σ，避免未来函数
        hist = self.spread_series.get(size=self.p.win + 1)[:-1]  # 不含当根
        sigma = np.std(hist, ddof=1)
        if np.isnan(sigma) or sigma == 0:
            return

        kappa = self.p.k_coeff * sigma
        h     = self.p.h_coeff * sigma
        s_t   = self.spread_series[0]

        # 3) 更新正/负累积和
        self.g_pos = max(0, self.g_pos + s_t - kappa)
        self.g_neg = max(0, self.g_neg - s_t - kappa)

        position_size = self.getposition(self.data0).size

        # 4) 开仓逻辑——当 g 超过 h
        if position_size == 0:
            # 计算动态配比（与原来一致）
            beta_now = self.data2.beta[0]
            if pd.isna(beta_now) or beta_now <= 0:
                return
            self.size0 = 10
            self.size1 = round(beta_now * 10)

            if self.g_pos > h:                    # 价差持续走高 → 做空价差
                self._open_position(short=True)
                self.g_pos = self.g_neg = 0       # 归零累积和
            elif self.g_neg > h:                  # 价差持续走低 → 做多价差
                self._open_position(short=False)
                self.g_pos = self.g_neg = 0
        else:
            # 5) 平仓逻辑——价差回到 0 附近
            if position_size > 0 and abs(s_t) < kappa:
                self._close_positions()
            elif position_size < 0 and abs(s_t) < kappa:
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

def run_strategy(data0, data1, data2, win, k_coeff, h_coeff, spread_window=60, initial_cash=100000):
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
            'win': win,
            'k_coeff': k_coeff,
            'h_coeff': h_coeff,
            'spread_window': spread_window
        }
    }


def grid_search(contract1, contract2, fromdate_str=None, todate_str=None,
               win_values=None, k_coeff_values=None, h_coeff_values=None, spread_windows=None,initial_cash=100000):
    """执行网格搜索找到最优参数"""
    data_file = 'D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5'
    # 读取数据
    print(f"从 {data_file} 读取 {contract1} 和 {contract2} 数据...")
    df0 = pd.read_hdf(data_file, key=contract1).reset_index()
    df1 = pd.read_hdf(data_file, key=contract2).reset_index()

    # 确保日期列格式正确
    df0['date'] = pd.to_datetime(df0['date'])
    df1['date'] = pd.to_datetime(df1['date'])

    # 设置回测日期范围
    if fromdate_str:
        fromdate = datetime.datetime.strptime(fromdate_str, "%Y-%m-%d")
    else:
        fromdate = datetime.datetime(2018, 1, 1)
        
    if todate_str:
        todate = datetime.datetime.strptime(todate_str, "%Y-%m-%d")
    else:
        todate = datetime.datetime(2025, 1, 1)
    
    print(f"回测日期范围: {fromdate.strftime('%Y-%m-%d')} 至 {todate.strftime('%Y-%m-%d')}")

    # 使用默认值或自定义参数值
    if win_values is None:
        win_values = [15, 20, 30]
    if k_coeff_values is None:
        k_coeff_values = [0.2, 0.4, 0.5, 0.6, 0.8]
    if h_coeff_values is None:
        h_coeff_values = [3.0, 5.0, 8.0, 10.0]
    if spread_windows is None:
        spread_windows = [20, 30, 60]
        
    print(f"网格搜索参数:")
    print(f"  窗口大小(win): {win_values}")
    print(f"  k系数(k_coeff): {k_coeff_values}")
    print(f"  h系数(h_coeff): {h_coeff_values}")
    print(f"  价差窗口(spread_window): {spread_windows}")
    

    
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
                    param_combinations.append((data0, data1, data2, win, k_coeff, h_coeff, spread_window))
    
    # 执行网格搜索
    results = []
    total_combinations = len(param_combinations)
    
    print(f"开始网格搜索，共{total_combinations}种参数组合...")
    
    for i, (data0, data1, data2, win, k_coeff, h_coeff, spread_window) in enumerate(param_combinations):
        print(f"测试参数组合 {i+1}/{total_combinations}: win={win}, k_coeff={k_coeff:.1f}, h_coeff={h_coeff:.1f}, spread_window={spread_window}")
        
        try:
            result = run_strategy(data0, data1, data2, win, k_coeff, h_coeff, spread_window, initial_cash)
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
        print(f"合约对: {contract1} - {contract2}")
        print(f"价差计算窗口: {best_result['params']['spread_window']}")
        print(f"Rolling窗口 (win): {best_result['params']['win']}")
        print(f"κ系数 (k_coeff): {best_result['params']['k_coeff']:.2f}")
        print(f"h系数 (h_coeff): {best_result['params']['h_coeff']:.2f}")
        print(f"夏普比率: {best_result['sharpe']:.4f}")
        print(f"最大回撤: {best_result['drawdown']:.2f}%")
        print(f"年化收益: {best_result['returns']:.2f}%")
        print(f"总收益率: {best_result['roi']:.2f}%")
        print(f"总交易次数: {best_result['total_trades']}")
        print(f"胜率: {best_result['win_rate']:.2f}%")
        

        # 显示所有结果，按夏普比率排序
        print("\n========= 所有参数组合结果（按夏普比率排序，仅显示前10个）=========")
        for i, result in enumerate(sorted_results[:10]):  # 只显示前10个最好的结果
            print(f"{i+1}. spread_window={result['params']['spread_window']}, "
                  f"win={result['params']['win']}, "
                  f"k_coeff={result['params']['k_coeff']:.2f}, "
                  f"h_coeff={result['params']['h_coeff']:.2f}, "
                  f"sharpe={result['sharpe']:.4f}, "
                  f"drawdown={result['drawdown']:.2f}%, "
                  f"return={result['returns']:.2f}%, "
                  f"win_rate={result['win_rate']:.2f}%")
        
        # 返回最佳结果
        return best_result
    else:
        print("未找到有效的参数组合")
        return None

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='期货合约对CUSUM策略参数优化工具')
    
    # 必需参数
    parser.add_argument('--contract1', required=True, help='第一个期货合约代码，例如 /OI')
    parser.add_argument('--contract2', required=True, help='第二个期货合约代码，例如 /Y')
    
    # 可选参数 - 日期范围
    parser.add_argument('--fromdate', help='回测开始日期，格式：YYYY-MM-DD')
    parser.add_argument('--todate', help='回测结束日期，格式：YYYY-MM-DD')
    
    # 可选参数 - 网格搜索参数
    parser.add_argument('--win', type=int, nargs='+', help='Rolling窗口大小列表，例如：15 20 30')
    parser.add_argument('--k-coeff', type=float, nargs='+', help='k系数列表，例如：0.2 0.5 0.8')
    parser.add_argument('--h-coeff', type=float, nargs='+', help='h系数列表，例如：3.0 5.0 8.0')
    parser.add_argument('--spread-window', type=int, nargs='+', help='价差计算窗口列表，例如：20 30 60')
    
    # 输出目录
    parser.add_argument('--output-dir', help='结果输出目录')
    
    # 初始资金
    parser.add_argument('--cash', type=float, default=100000, help='回测初始资金金额，默认：100000')
    
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    # 运行网格搜索
    grid_search(
        contract1=args.contract1,
        contract2=args.contract2,
        fromdate_str=args.fromdate,
        todate_str=args.todate,
        win_values=args.win,
        k_coeff_values=args.k_coeff,
        h_coeff_values=args.h_coeff,
        spread_windows=args.spread_window,
        initial_cash=args.cash
    )