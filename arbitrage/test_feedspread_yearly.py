import backtrader as bt
import pandas as pd
import numpy as np

import warnings
# warnings.filterwarnings("ignore", category=UserWarning)

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

# 1. 首先确认两个DataFrame的index是否相同
def check_and_align_data(df1, df2, date_column='date'):
    """
    检查并对齐两个DataFrame的数据
    """
    # 确保date列作为index
    if date_column in df1.columns:
        df1 = df1.set_index(date_column)
    if date_column in df2.columns:
        df2 = df2.set_index(date_column)
    
    # 找出共同的日期
    common_dates = df1.index.intersection(df2.index)
    
    # 检查是否有缺失的日期
    missing_in_df1 = df2.index.difference(df1.index)
    missing_in_df2 = df1.index.difference(df2.index)
    
    if len(missing_in_df1) > 0:
        print(f"在df_I中缺失的日期数: {len(missing_in_df1)}")
    if len(missing_in_df2) > 0:
        print(f"在df_RB中缺失的日期数: {len(missing_in_df2)}")
    
    # 对齐数据
    df1_aligned = df1.loc[common_dates]
    df2_aligned = df2.loc[common_dates]
    
    return df1_aligned, df2_aligned

# 2. 计算价差
def calculate_spread(df_I, df_RB, columns=['open', 'high', 'low', 'close', 'volume']):
    """
    计算两个DataFrame之间的价差
    """
    # 对齐数据
    df_I_aligned, df_RB_aligned = check_and_align_data(df_I, df_RB)
    
    # 创建价差DataFrame
    df_spread = pd.DataFrame(index=df_I_aligned.index)
    
    # 对每个列进行相减
    for col in columns:
        if col in df_I_aligned.columns and col in df_RB_aligned.columns:
            df_spread[f'{col}'] = 5*df_I_aligned[col] - df_RB_aligned[col]
    
    return df_spread.reset_index()

# 布林带策略
class SpreadBollingerStrategy(bt.Strategy):
    params = (
        ('period', 20),       # 布林带周期
        ('devfactor', 2),     # 布林带标准差倍数
        ('size_i', 5),        # 铁矿石交易规模
        ('size_rb', 1),       # 螺纹钢交易规模
    )
    
    def __init__(self):
        # 布林带指标
        self.boll = bt.indicators.BollingerBands(
            self.data2.close,  # 使用外部计算的价差
            period=self.p.period,
            devfactor=self.p.devfactor,
            subplot=False
        )
        
        # 交易状态
        self.order = None
        
        # 记录交易信息
        self.trades = []
        self.current_trade = None
        
        # 记录每年的净值
        self.year_values = {}
        
    def next(self):
        # 如果有未完成订单，跳过
        if self.order:
            return
            
        # 获取当前价差
        spread = self.data2.close[0]
        upper = self.boll.lines.top[0]
        lower = self.boll.lines.bot[0]
        
        # 交易逻辑
        if not self.position:
            # 开仓条件
            if spread > upper:
                # 做空价差：卖I买RB
                self.sell(data=self.data0, size=self.p.size_i)  # 卖5手I
                self.buy(data=self.data1, size=self.p.size_rb)  # 买1手RB
                self.current_trade = {
                    'entry_date': self.data.datetime.date(0),
                    'entry_price': spread,
                    'type': 'short'
                }
                
            elif spread < lower:
                # 做多价差：买I卖RB
                self.buy(data=self.data0, size=self.p.size_i)   # 买5手I
                self.sell(data=self.data1, size=self.p.size_rb) # 卖1手RB
                self.current_trade = {
                    'entry_date': self.data.datetime.date(0),
                    'entry_price': spread,
                    'type': 'long'
                }
                
        else:
            # 平仓条件
            if (spread <= self.boll.lines.mid[0] and self.position.size > 0) or \
               (spread >= self.boll.lines.mid[0] and self.position.size < 0):
                self.close(data=self.data0)
                self.close(data=self.data1)
                if self.current_trade:
                    self.current_trade['exit_date'] = self.data.datetime.date(0)
                    self.current_trade['exit_price'] = spread
                    self.current_trade['pnl'] = (spread - self.current_trade['entry_price']) * (-1 if self.current_trade['type'] == 'short' else 1)
                    self.trades.append(self.current_trade)
                    self.current_trade = None

    def notify_order(self, order):
        # 订单状态通知
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None

    def stop(self):
        # 按年计算最大回撤和夏普比率
        self.calculate_annual_metrics()
        
        # 输出交易详情
        self.print_trade_details()
        
        # 输出年度指标
        self.print_annual_metrics()

    def calculate_annual_metrics(self):
        # 按年分组计算净值
        for trade in self.trades:
            year = trade['entry_date'].year
            if year not in self.year_values:
                self.year_values[year] = []
            self.year_values[year].append(trade['pnl'])
        
        # 计算每年的最大回撤和夏普比率
        self.annual_metrics = {}
        for year, pnls in self.year_values.items():
            cumulative_pnl = np.cumsum(pnls)
            max_drawdown = (np.maximum.accumulate(cumulative_pnl) - cumulative_pnl).max()
            sharpe_ratio = np.mean(pnls) / np.std(pnls) if np.std(pnls) != 0 else 0
            self.annual_metrics[year] = {
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio
            }

    def print_trade_details(self):
        print("\n交易详情:")
        print("=" * 80)
        print("{:<12} {:<12} {:<12} {:<12} {:<12} {:<12}".format(
            "类型", "入场日期", "入场价", "出场日期", "出场价", "盈亏"
        ))
        for trade in self.trades:
            print("{:<12} {:<12} {:<12.2f} {:<12} {:<12.2f} {:<12.2f}".format(
            trade['type'],  # 交易类型
            trade['entry_date'].strftime('%Y-%m-%d'),  # 入场日期
            trade['entry_price'],  # 入场价
            trade['exit_date'].strftime('%Y-%m-%d'),  # 出场日期
            trade['exit_price'],  # 出场价
            trade['pnl']  # 盈亏
            ))

    def print_annual_metrics(self):
        print("\n年度指标:")
        print("=" * 80)
        print("{:<8} {:<12} {:<12}".format("年份", "最大回撤", "夏普比率"))
        for year, metrics in self.annual_metrics.items():
            print("{:<8} {:<12.2f} {:<12.2f}".format(
                year,
                metrics['max_drawdown'],
                metrics['sharpe_ratio']
            ))

# 使用示例
# 读取数据
output_file = 'D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5'
df_I = pd.read_hdf(output_file, key='/I').reset_index()
df_RB = pd.read_hdf(output_file, key='/RB').reset_index()

# 计算价差
df_spread = calculate_spread(df_I, df_RB)

# 显示结果
print("\n数据对齐后的形状:")
print(f"价差数据形状: {df_spread.shape}")
print("\n前几行数据:")
print(df_spread.head())

# 检查是否有缺失值
print("\n缺失值统计:")
print(df_spread.isnull().sum())

# 基本统计信息
print("\n基本统计信息:")
print(df_spread.describe())

# 添加数据
data0 = bt.feeds.PandasData(dataname=df_I, datetime='date', nocase=True)
data1 = bt.feeds.PandasData(dataname=df_RB, datetime='date', nocase=True)
data2 = bt.feeds.PandasData(dataname=df_spread, datetime='date', nocase=True)

# 创建回测引擎
cerebro = bt.Cerebro()
cerebro.adddata(data0, name='I')
cerebro.adddata(data1, name='RB')
cerebro.adddata(data2, name='spread')

# 添加策略
cerebro.addstrategy(SpreadBollingerStrategy)

# 设置初始资金
cerebro.broker.setcash(1000000.0)

# 运行回测
cerebro.run(oldsync=True)

# 绘制结果
cerebro.plot(volume=False, spread=True)
# cerebro.plot(volume=False)



