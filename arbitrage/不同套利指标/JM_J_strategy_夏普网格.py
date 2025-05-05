import backtrader as bt
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import seaborn as sns


# 夏普差值布林带策略
class SharpeDiffStrategy(bt.Strategy):
    params = (
        ('return_period', 15),       # 计算收益率的周期（15日收益率）
        ('ma_period', 10),          # 计算移动平均的周期（20日移动平均线）
        ('entry_std_multiplier', 0.3),  # 开仓标准差乘数
        ('max_hold_days', 15),     # 最大持仓天数
        ('printlog', False),
    )

    def __init__(self):
        # 存储夏普比率序列用于绘图
        self.sharpe_j_values = []
        self.sharpe_jm_values = []
        self.delta_sharpe_values = []
        self.dates = []
        
        # 布林带数据
        self.delta_sharpe_ma = []  # 移动平均
        self.delta_sharpe_std = []  # 标准差
        self.upper_band = []       # 上轨
        self.lower_band = []       # 下轨
        
        # 存储J和JM的收益率序列
        self.returns_j = []
        self.returns_jm = []
        
        # 初始化交易相关变量
        self.order = None
        self.position_type = None
        self.entry_day = 0
        
        # 存储历史价格数据
        self.j_prices = []
        self.jm_prices = []

    def next(self):
        if self.order: 
            return
            
        # 添加日期到列表
        self.dates.append(self.data0.datetime.date())
            
        # 保存最新价格
        self.j_prices.append(self.data0.close[0])
        self.jm_prices.append(self.data1.close[0])
        
        # 当价格数据不足时，跳过
        if len(self.j_prices) < self.p.return_period + 1:
            return
        
        # 计算15日收益率
        j_ret_15d = (self.j_prices[-1] / self.j_prices[-self.p.return_period-1]) - 1
        jm_ret_15d = (self.jm_prices[-1] / self.jm_prices[-self.p.return_period-1]) - 1
        
        # 保存每日收益率用于计算波动率
        if len(self) > 1:  # 确保有前一个价格
            ret_j = (self.data0.close[0] / self.data0.close[-1]) - 1
            ret_jm = (self.data1.close[0] / self.data1.close[-1]) - 1
            self.returns_j.append(ret_j)
            self.returns_jm.append(ret_jm)
        else:
            return  # 第一个bar没有前一天价格，跳过
        
        # 当收益率数据不足时，跳过
        if len(self.returns_j) < self.p.return_period:
            return
            
        # 计算15日波动率
        j_vol_15d = np.std(self.returns_j[-self.p.return_period:]) * np.sqrt(self.p.return_period)
        jm_vol_15d = np.std(self.returns_jm[-self.p.return_period:]) * np.sqrt(self.p.return_period)
        
        # 计算夏普比率
        sharpe_j = j_ret_15d / j_vol_15d if j_vol_15d > 0 else 0
        sharpe_jm = jm_ret_15d / jm_vol_15d if jm_vol_15d > 0 else 0
        
        # 存储夏普比率用于绘图
        self.sharpe_j_values.append(sharpe_j)
        self.sharpe_jm_values.append(sharpe_jm)
        
        # 计算夏普差值 ΔSharpe = μJ/σJ - μJM/σJM
        delta_sharpe = sharpe_j - sharpe_jm
        self.delta_sharpe_values.append(delta_sharpe)
        
        # 计算20日移动平均和标准差
        if len(self.delta_sharpe_values) >= self.p.ma_period:
            # 计算20日移动平均 MA(ΔSharpe) = MA20(ΔSharpe)
            ma_delta = np.mean(self.delta_sharpe_values[-self.p.ma_period:])
            self.delta_sharpe_ma.append(ma_delta)
            
            # 计算20日标准差 σΔSharpe = Std20(ΔSharpe)
            std_delta = np.std(self.delta_sharpe_values[-self.p.ma_period:])
            self.delta_sharpe_std.append(std_delta)
            
            # 计算布林带上下轨
            # Upper Band = MAΔSharpe + 2 × σΔSharpe
            upper = ma_delta + self.p.entry_std_multiplier * std_delta
            self.upper_band.append(upper)
            
            # Lower Band = MAΔSharpe - 2 × σΔSharpe
            lower = ma_delta - self.p.entry_std_multiplier * std_delta
            self.lower_band.append(lower)
        else:
            # 数据不足以计算移动平均和标准差时，跳过
            return
        
        # 交易逻辑 - 基于夏普差值与布林带的关系

        if self.position_type is not None:
            days_in_trade = len(self) - self.entry_day
            
            # 根据持仓方向和夏普差值决定是否平仓
            if (self.position_type == 'long_j_short_jm' and delta_sharpe >= ma_delta) or days_in_trade >= self.p.max_hold_days:
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(f'平仓: J-JM夏普差={delta_sharpe:.4f}, 持仓天数={days_in_trade}, 均值={ma_delta:.4f}')
            
            elif (self.position_type == 'short_j_long_jm' and delta_sharpe <= ma_delta) or days_in_trade >= self.p.max_hold_days:
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(f'平仓: J-JM夏普差={delta_sharpe:.4f}, 持仓天数={days_in_trade}, 均值={ma_delta:.4f}')
                
        else:
            # 开仓逻辑
            if delta_sharpe >= upper:
                # 夏普差值突破上轨，做多J，做空JM
                self.order = self.buy(data=self.data0, size=10)
                self.order = self.sell(data=self.data1, size=14)
                self.entry_day = len(self)
                self.position_type = 'long_j_short_jm'
                if self.p.printlog:
                    print(f'开仓: 做多J，做空JM, 夏普差={delta_sharpe:.4f}, 上轨={upper:.4f}')
                
            elif delta_sharpe <= lower:
                # 夏普差值突破下轨，做空J，做多JM
                self.order = self.sell(data=self.data0, size=10)
                self.order = self.buy(data=self.data1, size=14)
                self.entry_day = len(self)
                self.position_type = 'short_j_long_jm'
                if self.p.printlog:
                    print(f'开仓: 做空J，做多JM, 夏普差={delta_sharpe:.4f}, 下轨={lower:.4f}')

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if self.p.printlog:
                if order.isbuy():
                    print(f'买入执行: 价格={order.executed.price:.2f}, 成本={order.executed.value:.2f}, 手续费={order.executed.comm:.2f}')
                else:
                    print(f'卖出执行: 价格={order.executed.price:.2f}, 成本={order.executed.value:.2f}, 手续费={order.executed.comm:.2f}')
                    
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print('订单被取消/拒绝')
            
        self.order = None

# 数据加载函数，处理索引问题
def load_data(symbol1, symbol2, fromdate, todate):
    output_file = 'D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5'
    
    try:
        # 加载数据时不保留原有索引结构
        df0 = pd.read_hdf(output_file, key=symbol1).reset_index()
        df1 = pd.read_hdf(output_file, key=symbol2).reset_index()
        
        # 查找日期列（兼容不同命名）
        date_col = [col for col in df0.columns if 'date' in col.lower()]
        if not date_col:
            raise ValueError("数据集中未找到日期列")
        
        # 设置日期索引
        df0 = df0.set_index(pd.to_datetime(df0[date_col[0]]))
        df1 = df1.set_index(pd.to_datetime(df1[date_col[0]]))
        df0 = df0.sort_index().loc[fromdate:todate]
        df1 = df1.sort_index().loc[fromdate:todate]
        
        # 创建数据feed
        data0 = bt.feeds.PandasData(
            dataname=df0,
            datetime=None,  # 使用索引
            open='open', high='high', low='low', close='close', volume='volume'
        )
        data1 = bt.feeds.PandasData(
            dataname=df1,
            datetime=None,
            open='open', high='high', low='low', close='close', volume='volume'
        )
        return data0, data1
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None, None

# 运行网格回测并绘制热力图
def run_grid_search():
    # 定义参数网格
    ma_periods = [5, 10, 15, 20, 25, 30, 35, 40]  # 移动平均周期
    entry_multipliers = [0.1, 0.2, 0.3, 0.4, 0.5, 0.8, 1.0, 1.5]  # 标准差乘数
    
    # 存储结果
    results = np.zeros((len(ma_periods), len(entry_multipliers)))
    
    # 设置初始日期
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)
    
    # 加载数据一次（这些数据可以重复使用）
    data0, data1 = load_data('/J', '/JM', fromdate, todate)
    
    if data0 is None or data1 is None:
        print("无法加载数据，请检查文件路径和数据格式")
        return
    
    print("开始网格回测...")
    print(f"测试参数组合: {len(ma_periods)} x {len(entry_multipliers)} = {len(ma_periods) * len(entry_multipliers)}个组合")
    
    # 进行网格回测
    for i, ma_period in enumerate(ma_periods):
        for j, entry_multiplier in enumerate(entry_multipliers):
            print(f"测试参数: ma_period={ma_period}, entry_std_multiplier={entry_multiplier}")
            
            try:
                # 创建一个新的cerebro实例
                cerebro = bt.Cerebro(stdstats=False)
                
                # 添加相同的数据
                cerebro.adddata(data0, name='J')
                cerebro.adddata(data1, name='JM')
                
                # 添加策略，使用当前测试的参数
                cerebro.addstrategy(SharpeDiffStrategy, 
                                    ma_period=ma_period, 
                                    entry_std_multiplier=entry_multiplier,
                                    printlog=False)  # 关闭日志，减少输出
                
                # 设置资金和佣金
                cerebro.broker.setcash(100000)
                cerebro.broker.setcommission(commission=0.0003)
                cerebro.broker.set_shortcash(False)
                
                # 添加夏普比率分析器
                cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                                    timeframe=bt.TimeFrame.Days,
                                    riskfreerate=0,
                                    annualize=True)
                
                # 运行回测
                strats = cerebro.run()
                
                # 获取夏普比率 - 安全处理None值
                sharpe_analysis = strats[0].analyzers.sharperatio.get_analysis()
                sharpe = sharpe_analysis.get('sharperatio', 0) if sharpe_analysis else 0
                
                # 存储结果
                results[i, j] = sharpe
                
                print(f"夏普比率: {sharpe:.2f}")
            except Exception as e:
                print(f"参数组合 ma_period={ma_period}, entry_std_multiplier={entry_multiplier} 执行出错: {e}")
                results[i, j] = -99  # 使用一个明显的负值标记出错项
    
    # 绘制热力图
    plt.figure(figsize=(12, 8))
    
    # 使用Seaborn的热力图
    ax = sns.heatmap(results, 
                     annot=True, 
                     fmt=".2f", 
                     cmap="YlGnBu", 
                     xticklabels=entry_multipliers, 
                     yticklabels=ma_periods)
    
    # 设置标题和标签
    plt.title('sharpe_ratio_heatmap - ma_period vs entry_std_multiplier')
    plt.xlabel('entry_std_multiplier')
    plt.ylabel('ma_period')
    
    # 显示图形
    plt.tight_layout()
    plt.savefig('sharpe_ratio_heatmap.png')
    plt.show()
    
    print("热力图已保存为 'sharpe_ratio_heatmap.png'")
    
    # 清除无效值(出错的回测结果)
    results_clean = np.copy(results)
    results_clean[results_clean == -99] = np.nan
    
    # 找出最佳参数组合（排除无效值）
    if np.any(~np.isnan(results_clean)):
        max_i, max_j = np.unravel_index(np.nanargmax(results_clean), results_clean.shape)
        best_ma_period = ma_periods[max_i]
        best_entry_multiplier = entry_multipliers[max_j]
        best_sharpe = results_clean[max_i, max_j]
        
        print(f"\n最佳参数组合:")
        print(f"ma_period: {best_ma_period}")
        print(f"entry_std_multiplier: {best_entry_multiplier}")
        print(f"夏普比率: {best_sharpe:.4f}")
    else:
        print("\n所有参数组合都出现错误，无法确定最佳参数")
    
    return results, ma_periods, entry_multipliers

# 修改主函数，调用网格搜索
if __name__ == '__main__':
    run_grid_search()
