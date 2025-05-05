import pandas as pd
import numpy as np

# 读取数据
output_file = 'D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5'
df_I = pd.read_hdf(output_file, key='/I').reset_index()
df_RB = pd.read_hdf(output_file, key='/RB').reset_index()

# 检查并对齐数据
def check_and_align_data(df1, df2, date_column='date'):
    if date_column in df1.columns:
        df1 = df1.set_index(date_column)
    if date_column in df2.columns:
        df2 = df2.set_index(date_column)
    
    common_dates = df1.index.intersection(df2.index)
    
    df1_aligned = df1.loc[common_dates]
    df2_aligned = df2.loc[common_dates]
    
    return df1_aligned, df2_aligned

# 计算价差
def calculate_spread(df_I, df_RB, columns=['open', 'high', 'low', 'close', 'volume']):
    df_I_aligned, df_RB_aligned = check_and_align_data(df_I, df_RB)
    df_spread = pd.DataFrame(index=df_I_aligned.index)
    
    for col in columns:
        if col in df_I_aligned.columns and col in df_RB_aligned.columns:
            df_spread[f'{col}'] = 5 * df_I_aligned[col] - df_RB_aligned[col]
    
    return df_spread.reset_index()

# 计算年化夏普比率
def annualized_sharpe_ratio(returns, risk_free_rate=0.01):
    excess_returns = returns - risk_free_rate / 252  # daily risk-free rate
    mean_return = excess_returns.mean()
    std_dev = excess_returns.std()
    sharpe_ratio = mean_return / std_dev
    annual_sharpe = sharpe_ratio * np.sqrt(252)  # annualizing
    return annual_sharpe

# 计算最大回撤
def max_drawdown(nav):
    running_max = np.maximum.accumulate(nav)
    drawdowns = (nav - running_max) / running_max
    max_drawdown = drawdowns.min()  # 最大回撤
    return max_drawdown

# 模拟回测
df_spread = calculate_spread(df_I, df_RB)

# 使用布林带策略进行交易
period = 20  # 布林带周期
devfactor = 2  # 布林带标准差倍数

# 计算布林带
df_spread['rolling_mean'] = df_spread['close'].rolling(window=period).mean()
df_spread['rolling_std'] = df_spread['close'].rolling(window=period).std()
df_spread['upper'] = df_spread['rolling_mean'] + devfactor * df_spread['rolling_std']
df_spread['lower'] = df_spread['rolling_mean'] - devfactor * df_spread['rolling_std']

# 初始化资金和仓位
initial_cash = 1000000
cash = initial_cash
position = 0  # 0表示没有仓位，1表示多仓，-1表示空仓
trade_pnl = []  # 记录每次交易的盈亏

# 计算每日收益
returns = []

# 模拟交易
for i in range(period, len(df_spread)):
    spread = df_spread['close'].iloc[i]
    upper = df_spread['upper'].iloc[i]
    lower = df_spread['lower'].iloc[i]
    
    # 开仓条件
    if position == 0:
        if spread > upper:  # 做空
            position = -1
            entry_price = spread
        elif spread < lower:  # 做多
            position = 1
            entry_price = spread
    # 平仓条件
    elif position == 1 and spread >= df_spread['rolling_mean'].iloc[i]:
        # 做多平仓
        pnl = (spread - entry_price) * 5  # 交易规模为5
        trade_pnl.append(pnl)
        cash += pnl
        position = 0
    elif position == -1 and spread <= df_spread['rolling_mean'].iloc[i]:
        # 做空平仓
        pnl = (entry_price - spread) * 5  # 交易规模为5
        trade_pnl.append(pnl)
        cash += pnl
        position = 0
    
    # 计算每日收益
    daily_return = (cash - initial_cash) / initial_cash
    returns.append(daily_return)

# 计算年化夏普比率和最大回撤
nav = np.array([initial_cash + sum(trade_pnl[:i+1]) for i in range(len(trade_pnl))])
annual_sharpe = annualized_sharpe_ratio(np.array(returns))
max_dd = max_drawdown(nav)

# 打印结果
print(f"年化夏普比率: {annual_sharpe:.2f}")
print(f"最大回撤: {max_dd:.2%}")
