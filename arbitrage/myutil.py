import pandas as pd
import numpy as np

import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller


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
def calculate_spread(df1, df2, factor1=5,factor2=1, columns=['open', 'high', 'low', 'close', 'volume']):
    """
    计算两个DataFrame之间的价差
    :param df1: 第一个DataFrame
    :param df2: 第二个DataFrame
    :param columns: 需要计算价差的列
    :param factor: 价差计算时的乘数因子
    :return: 包含价差的DataFrame
    """
    # 对齐数据
    df1_aligned, df2_aligned = check_and_align_data(df1, df2)

    # 创建价差DataFrame
    df_spread = pd.DataFrame(index=df1_aligned.index)

    # 对每个列进行相减
    for col in columns:
        if col in df1_aligned.columns and col in df2_aligned.columns:
            df_spread[f'{col}'] = factor1 * df1_aligned[col] - factor2*df2_aligned[col]

    return df_spread.reset_index()



def calculate_volatility_ratio(price_c, price_d, mc, md):
    """
    波动率匹配持仓比例（整数版）
    :param price_c: 品种C价格序列（pd.Series）
    :param price_d: 品种D价格序列（pd.Series）
    :param mc: 品种C合约乘数
    :param md: 品种D合约乘数
    :return: 整数配比 (Nc, Nd)
    """
    # 对齐数据
    merged = pd.concat([price_c, price_d], axis=1).dropna()

    # 计算年化波动率（假设日频数据）
    vol_c = np.log(merged.iloc[:, 0] / merged.iloc[:, 0].shift(1)).std() * np.sqrt(252)
    vol_d = np.log(merged.iloc[:, 1] / merged.iloc[:, 1].shift(1)).std() * np.sqrt(252)

    # 获取最新价格
    pc = merged.iloc[-1, 0]
    pd = merged.iloc[-1, 1]

    # 计算理论配比
    ratio = (vol_c * mc * pc) / (vol_d * md * pd)

    # 返回最简整数比
    return simplify_ratio(ratio)


def simplify_ratio(ratio, max_denominator=10):
    """
    将浮点比例转换为最简整数比
    :param ratio: 浮点比例值
    :param max_denominator: 最大允许的分母值
    :return: (分子, 分母) 的元组
    """
    from fractions import Fraction
    frac = Fraction(ratio).limit_denominator(max_denominator)
    return (frac.numerator, frac.denominator)

class KalmanFilter:
    def __init__(self):
        self.x = np.array([1.0])  # 初始系数（假设1:1配比）
        self.P = np.eye(1)        # 状态协方差
        self.Q = 0.01             # 过程噪声
        self.R = 0.1              # 观测噪声

    def update(self, z):
        # 预测步骤
        x_pred = self.x
        P_pred = self.P + self.Q

        # 更新步骤
        K = P_pred / (P_pred + self.R)
        self.x = x_pred + K * (z - x_pred)
        self.P = (1 - K) * P_pred
        return self.x[0]

def kalman_ratio(df1, df2):
    kf = KalmanFilter()
    spreads = []
    for p1, p2 in zip(df1, df2):
        if p2 != 0:
            ratio = p1 / p2  # 实时价格比
            beta = kf.update(ratio)
        spreads.append(p1 - beta * p2)

    # 取末段均值确定整数配比
    final_beta = np.mean(kf.x[-30:]) if len(df1) >30 else round(kf.x[-1])
    return simplify_ratio(final_beta), np.array(spreads)


def cointegration_ratio(df1, df2):

    # 协整回归
    X = sm.add_constant(df2)
    model = sm.OLS(df1, X).fit()
    beta = model.params[1] # 回归系数整数化
    spread = df1 - beta * df2  # 价差序列

    return simplify_ratio(beta), spread  # 配比格式(资产1单位:资产β单位)

