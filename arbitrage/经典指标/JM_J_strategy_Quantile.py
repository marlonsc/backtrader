import backtrader as bt
import pandas as pd
import numpy as np
import sys
import os
import datetime
import argparse

from arbitrage.myutil import calculate_spread, check_and_align_data, cointegration_ratio
# https://mp.weixin.qq.com/s/na-5duJiRM1fTJF0WrcptA

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='分位数策略参数')
    
    # 必须参数
    parser.add_argument('--window', type=int, default=60, help='计算滚动价差的窗口大小')
    parser.add_argument('--df0_key', type=str, default='/J', help='第一个数据集的键值')
    parser.add_argument('--df1_key', type=str, default='/JM', help='第二个数据集的键值')
    parser.add_argument('--fromdate', type=str, default='2018-01-01', help='回测开始日期')
    parser.add_argument('--todate', type=str, default='2025-01-01', help='回测结束日期')
    
    # 策略参数
    parser.add_argument('--lookback_period', type=int, default=120, help='回看周期')
    parser.add_argument('--upper_quantile', type=float, default=0.95, help='上轨分位数')
    parser.add_argument('--lower_quantile', type=float, default=0.05, help='下轨分位数')
    parser.add_argument('--max_positions', type=int, default=3, help='最大加仓次数')
    parser.add_argument('--add_position_threshold', type=float, default=0.5, help='加仓阈值（相对于轨道的百分比）')
    
    # 其他参数
    parser.add_argument('--setcash', type=float, default=300000, help='初始资金')
    parser.add_argument('--plot', type=lambda x: x.lower() == 'true', default=True, help='是否绘制结果(True/False)')
    parser.add_argument('--setslippage', type=float, default=0.0, help='设置滑点率')
    parser.add_argument('--export_csv', type=lambda x: x.lower() == 'true', default=False, help='是否导出回测数据到CSV(True/False)')
    parser.add_argument('--verbose', type=lambda x: x.lower() == 'true', default=True, help='是否输出详细信息(True/False)')
    
    return parser.parse_args()

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

# 读取数据
output_file = '/Users/f/Desktop/ricequant/1d_2017to2024_noadjust.h5'
df0 = pd.read_hdf(output_file, key='/J').reset_index()
df1 = pd.read_hdf(output_file, key='/JM').reset_index()

# 确保日期列格式正确
df0['date'] = pd.to_datetime(df0['date'])
df1['date'] = pd.to_datetime(df1['date'])

# 计算滚动价差
df_spread = calculate_rolling_spread(df0, df1, window=90)
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

# 创建分位数指标（自定义）
class QuantileIndicator(bt.Indicator):
    lines = ('upper', 'lower', 'mid')
    params = (
        ('period', 30),
        ('upper_quantile', 0.85),  # 上轨分位数
        ('lower_quantile', 0.15),  # 下轨分位数
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
        ('lookback_period', 30),       # 回看周期
        ('upper_quantile', 0.8),       # 上轨分位数
        ('lower_quantile', 0.2),       # 下轨分位数
        ('max_positions', 3),          # 最大加仓次数
        ('add_position_threshold', 0.1),  # 加仓阈值（相对于轨道的百分比）
        ('verbose', True),             # 是否打印详细信息
    )

    def __init__(self):
        # 计算价差的分位数指标
        self.quantile = QuantileIndicator(
            self.data2.close, 
            period=self.p.lookback_period,
            upper_quantile=self.p.upper_quantile,
            lower_quantile=self.p.lower_quantile,
            subplot=True
        )
        
        # 交易状态
        self.order = None
        self.entry_price = 0
        self.entry_direction = None  # 持仓方向：'long'/'short'
        self.position_layers = 0     # 当前持仓层数
        
        # 保存每日收益数据（用于导出CSV）
        self.record_dates = []
        self.record_data = []
        self.prev_portfolio_value = self.broker.getvalue()

    def next(self):
        # 记录每日收益率数据
        current_value = self.broker.getvalue()
        daily_return = (current_value / self.prev_portfolio_value) - 1.0 if self.prev_portfolio_value > 0 else 0
        self.prev_portfolio_value = current_value
        
        self.record_dates.append(self.datetime.date())
        self.record_data.append({
            'date': self.datetime.date(),
            'close': self.data2.close[0],
            'upper_band': self.quantile.upper[0],
            'lower_band': self.quantile.lower[0],
            'mid_band': self.quantile.mid[0],
            'portfolio_value': current_value,
            'daily_return': daily_return,
            'position': self.getposition(self.data0).size,
            'beta': self.data2.beta[0],
            'position_layers': self.position_layers
        })
        
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
            if self.p.verbose:
                print(f'加仓做多J {add_size0}手, 做空JM {add_size1}手')
            self.buy(data=self.data0, size=add_size0)
            self.sell(data=self.data1, size=add_size1)
        else:
            if self.p.verbose:
                print(f'加仓做空J {add_size0}手, 做多JM {add_size1}手')
            self.sell(data=self.data0, size=add_size0)
            self.buy(data=self.data1, size=add_size1)
        self.position_layers += 1

    def _close_positions(self):
        '''平仓'''
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
    
    def get_backtest_data(self):
        """获取回测数据，用于导出到CSV"""
        return pd.DataFrame(self.record_data)

def main():
    # 解析命令行参数
    args = parse_args()
    print(f"解析参数: {args}")
    
    # 读取数据
    output_file = '/Users/f/Desktop/ricequant/1d_2017to2024_noadjust.h5'
    df0 = pd.read_hdf(output_file, key=args.df0_key).reset_index()
    df1 = pd.read_hdf(output_file, key=args.df1_key).reset_index()

    # 确保日期列格式正确
    df0['date'] = pd.to_datetime(df0['date'])
    df1['date'] = pd.to_datetime(df1['date'])

    # 计算滚动价差
    df_spread = calculate_rolling_spread(df0, df1, window=args.window)
    print("滚动价差计算完成，系数示例：")
    print(df_spread.head())

    # 设置回测日期
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    # 添加数据
    data0 = bt.feeds.PandasData(dataname=df0, datetime='date', nocase=True, fromdate=fromdate, todate=todate)
    data1 = bt.feeds.PandasData(dataname=df1, datetime='date', nocase=True, fromdate=fromdate, todate=todate)
    data2 = SpreadData(dataname=df_spread, fromdate=fromdate, todate=todate)

    # 创建回测引擎
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(data0, name=args.df0_key.replace('/', ''))
    cerebro.adddata(data1, name=args.df1_key.replace('/', ''))
    cerebro.adddata(data2, name='spread')

    # 添加策略
    cerebro.addstrategy(DynamicSpreadQuantileStrategy,
                       lookback_period=args.lookback_period,
                       upper_quantile=args.upper_quantile,
                       lower_quantile=args.lower_quantile,
                       max_positions=args.max_positions,
                       add_position_threshold=args.add_position_threshold,
                       verbose=args.verbose)

    # 设置初始资金和滑点
    cerebro.broker.setcash(args.setcash)
    cerebro.broker.set_shortcash(False)
    cerebro.broker.set_slippage_perc(args.setslippage)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.DrawDown)  # 回撤分析器
    cerebro.addanalyzer(bt.analyzers.ROIAnalyzer, period=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                        timeframe=bt.TimeFrame.Days,  # 按日数据计算
                        riskfreerate=0,               # 风险无风险利率
                        annualize=True,               # 年化
                        )
    cerebro.addanalyzer(bt.analyzers.Returns,
                        tann=bt.TimeFrame.Days,  # 年化因子
                        )
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.CumValue)

    # 运行回测
    results = cerebro.run()
    strategy = results[0]  # 获取策略实例

    # 获取分析结果
    drawdown = strategy.analyzers.drawdown.get_analysis()
    sharpe = strategy.analyzers.sharperatio.get_analysis()
    roi = strategy.analyzers.roianalyzer.get_analysis()
    total_returns = strategy.analyzers.returns.get_analysis()  # 获取总回报率
    trade_stats = strategy.analyzers.tradeanalyzer.get_analysis()  # 交易统计

    # 打印分析结果
    print("=============回测结果================")
    print(f"\nSharpe Ratio: {sharpe.get('sharperatio', 0):.2f}")
    print(f"Drawdown: {drawdown.get('max', {}).get('drawdown', 0):.2f} %")
    print(f"Annualized/Normalized return: {total_returns.get('rnorm100', 0):.2f}%")
    print(f"Total compound return: {roi.get('roi100', 0):.2f}%")
    
    # 交易统计信息
    total_trades = trade_stats.get('total', {}).get('total', 0)
    win_trades = trade_stats.get('won', {}).get('total', 0)
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
    print(f"总交易次数: {total_trades}")
    print(f"胜率: {win_rate:.2f}%")
    
    # 导出CSV
    if args.export_csv:
        # 获取回测数据
        backtest_data = strategy.get_backtest_data()
        # 生成文件名
        params_str = f"period{args.lookback_period}_upper{args.upper_quantile}_lower{args.lower_quantile}"
        filename = f"outcome/Quantile_backtest_{args.df0_key.replace('/', '')}{args.df1_key.replace('/', '')}_{params_str}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # 保存CSV
        backtest_data.to_csv(filename, index=False)
        print(f"回测数据已保存至: {filename}")
    
    # 绘制结果
    if args.plot:
        cerebro.plot(volume=False, spread=True)

if __name__ == '__main__':
    main() 