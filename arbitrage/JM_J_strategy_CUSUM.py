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
    parser = argparse.ArgumentParser(description='CUSUM策略参数')
    
    # 必须参数
    parser.add_argument('--window', type=int, default=30, help='计算滚动价差的窗口大小')
    parser.add_argument('--df0_key', type=str, default='/J', help='第一个数据集的键值')
    parser.add_argument('--df1_key', type=str, default='/JM', help='第二个数据集的键值')
    parser.add_argument('--fromdate', type=str, default='2018-01-01', help='回测开始日期')
    parser.add_argument('--todate', type=str, default='2025-01-01', help='回测结束日期')
    parser.add_argument('--win', type=int, default=30, help='策略中的滚动窗口')
    parser.add_argument('--k_coeff', type=float, default=0.6, help='kappa系数')
    parser.add_argument('--h_coeff', type=float, default=3.0, help='h系数')
    parser.add_argument('--setcash', type=float, default=100000, help='初始资金')
    parser.add_argument('--plot', type=lambda x: x.lower() == 'true', default=True, help='是否绘制结果(True/False)')
    parser.add_argument('--setslippage', type=float, default=0.0, help='设置滑点率')
    parser.add_argument('--export_csv', type=lambda x: x.lower() == 'true', default=False, help='是否导出回测数据到CSV(True/False)')
    
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
        ('win', 30),          # rolling 窗口
        ('k_coeff', 0.6),     # κ = k_coeff * σ
        ('h_coeff', 3.0),     # h = h_coeff * σ
    )

    def __init__(self):
        # 保存两条累积和
        self.g_pos, self.g_neg = 0.0, 0.0          # CUSUM state
        # 方便读取最近 win 根价差
        self.spread_series = self.data2.close
        
        # 保存每日收益数据
        self.record_dates = []
        self.record_data = []
        self.prev_portfolio_value = self.broker.getvalue()

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
        # 记录当前日期
        current_date = self.data0.datetime.date(0)
        
        # 记录当日数据
        pos0 = self.getposition(self.data0).size
        pos1 = self.getposition(self.data1).size
        
        # 计算每日收益
        current_value = self.broker.getvalue()
        daily_return = (current_value / self.prev_portfolio_value) - 1.0 if self.prev_portfolio_value > 0 else 0.0
        self.prev_portfolio_value = current_value
        
        # 将数据收集到一个列表中
        self.record_dates.append(current_date)
        self.record_data.append({
            'date': current_date,
            f'{self.data0._name}_close': self.data0.close[0],
            f'{self.data1._name}_close': self.data1.close[0],
            'spread': self.data2.close[0],
            'beta': self.data2.beta[0],
            f'{self.data0._name}_position': pos0,
            f'{self.data1._name}_position': pos1,
            'daily_return': round(daily_return, 8)
        })
        
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
            # 5) 优化平仓逻辑：动态退出阈值
            exit_threshold = max(kappa, 0.25*sigma)  # 取较大值避免频繁平仓
            if position_size > 0:
                if s_t < -exit_threshold:  # 多头平仓条件加强
                    self._close_positions()
            elif position_size < 0:
                if s_t > exit_threshold:   # 空头平仓条件加强
                    self._close_positions()

    def notify_trade(self, trade):
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
    output_file = 'D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5'
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
    cerebro.addstrategy(DynamicSpreadCUSUMStrategy,
                        win=args.win,
                        k_coeff=args.k_coeff,
                        h_coeff=args.h_coeff)

    # 设置初始资金和滑点
    cerebro.broker.setcash(args.setcash)
    cerebro.broker.set_shortcash(False)
    cerebro.broker.set_slippage_perc(args.setslippage)
    
    # 添加分析器
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

    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.Cash)
    cerebro.addobserver(bt.observers.CumValue)

    # 运行回测
    results = cerebro.run()
    strategy = results[0]  # 获取策略实例

    # 获取分析结果
    drawdown = strategy.analyzers.drawdown.get_analysis()
    sharpe = strategy.analyzers.sharperatio.get_analysis()
    roi = strategy.analyzers.roianalyzer.get_analysis()
    total_returns = strategy.analyzers.returns.get_analysis()  # 获取总回报率
    cagr = strategy.analyzers.cagranalyzer.get_analysis()

    # 打印分析结果
    print("=============回测结果================")
    print(f"\nSharpe Ratio: {sharpe.get('sharperatio', 0):.2f}")
    print(f"Drawdown: {drawdown.get('max', {}).get('drawdown', 0):.2f} %")
    print(f"Annualized/Normalized return: {total_returns.get('rnorm100', 0):.2f}%")
    print(f"Total compound return: {roi.get('roi100', 0):.2f}%")
    print(f"年化收益: {cagr.get('cagr', 0):.2f} ")
    print(f"夏普比率: {cagr.get('sharpe', 0):.2f}")
    
    # 导出CSV
    if args.export_csv:
        # 获取回测数据
        backtest_data = strategy.get_backtest_data()
        # 生成文件名
        params_str = f"win{args.win}_k{args.k_coeff}_h{args.h_coeff}"
        filename = f"outcome/CUSUM_backtest_{args.df0_key.replace('/', '')}{args.df1_key.replace('/', '')}_{params_str}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        # 保存CSV
        backtest_data.to_csv(filename, index=False)
        print(f"回测数据已保存至: {filename}")
    
    # 绘制结果
    if args.plot:
        cerebro.plot(volume=False, spread=True)

if __name__ == '__main__':
    main() 