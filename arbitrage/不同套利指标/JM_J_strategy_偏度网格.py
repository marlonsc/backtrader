import backtrader as bt
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import seaborn as sns


# 偏度差均值回归策略（基于历史统计量的版本）
class SkewnessArbitrageStrategy(bt.Strategy):
    params = (
        ('skew_period', 20),       # 计算偏度的周期
        ('lookback_period', 60),   # 计算历史统计量的回看周期
        ('entry_std_multiplier', 1.5),  # 开仓标准差乘数
        ('exit_std_multiplier', 0.5),   # 平仓标准差乘数
        ('max_hold_days', 15),     # 最大持仓天数
        ('printlog', False),
    )

    def __init__(self):
        # 存储偏度序列用于绘图
        self.skew_j_values = []
        self.skew_jm_values = []
        self.delta_skew_values = []
        self.dates = []
        
        # 存储偏度差的历史统计量
        self.delta_mean = 0
        self.delta_std = 0
        
        # 存储开仓和平仓阈值
        self.upper_entry_threshold = 0
        self.lower_entry_threshold = 0
        self.upper_exit_threshold = 0
        self.lower_exit_threshold = 0
        
        # 为两个数据集创建收益率序列
        self.returns_j = []
        self.returns_jm = []
        
        # 初始化交易相关变量
        self.order = None
        self.position_type = None
        self.entry_day = 0
        

    def next(self):
        if self.order: 
            return
            
        # 添加日期到列表
        self.dates.append(self.data0.datetime.date())
            
        # 计算最新收益率
        if len(self) > 1:  # 确保有前一个价格
            ret_j = (self.data0.close[0] / self.data0.close[-1]) - 1
            ret_jm = (self.data1.close[0] / self.data1.close[-1]) - 1
            self.returns_j.append(ret_j)
            self.returns_jm.append(ret_jm)
        else:
            return  # 第一个bar没有前一天价格，跳过
        
        # 当收益率数据不足时，跳过
        if len(self.returns_j) < self.p.skew_period:
            return
            
        # 计算偏度 - 只保留最近的skew_period个收益率
        j_returns = np.array(self.returns_j[-self.p.skew_period:])
        jm_returns = np.array(self.returns_jm[-self.p.skew_period:])
        
        # 计算J合约偏度
        j_mean = np.mean(j_returns)
        j_std = np.std(j_returns)
        skew_j = np.mean((j_returns - j_mean)**3) / (j_std**3) if j_std > 0 else 0
        
        # 计算JM合约偏度
        jm_mean = np.mean(jm_returns)
        jm_std = np.std(jm_returns)
        skew_jm = np.mean((jm_returns - jm_mean)**3) / (jm_std**3) if jm_std > 0 else 0
        
        # 存储偏度值用于绘图
        self.skew_j_values.append(skew_j)
        self.skew_jm_values.append(skew_jm)
        
        # 计算当前的偏度差值
        current_delta = skew_j - skew_jm
        self.delta_skew_values.append(current_delta)
        
        # 计算历史偏度差的均值和标准差
        if len(self.delta_skew_values) >= self.p.lookback_period:
            hist_delta_values = np.array(self.delta_skew_values[-self.p.lookback_period:])
            self.delta_mean = np.mean(hist_delta_values)
            self.delta_std = np.std(hist_delta_values)
            
            # 更新开仓和平仓阈值
            self.upper_entry_threshold = self.delta_mean + self.p.entry_std_multiplier * self.delta_std
            self.lower_entry_threshold = self.delta_mean - self.p.entry_std_multiplier * self.delta_std
            self.upper_exit_threshold = self.delta_mean + self.p.exit_std_multiplier * self.delta_std
            self.lower_exit_threshold = self.delta_mean - self.p.exit_std_multiplier * self.delta_std
        else:
            # 数据不足以计算历史统计量时，跳过
            return
        
        # 交易逻辑 - 基于偏度差与历史均值的关系
        if self.position_type is not None:
            days_in_trade = len(self) - self.entry_day
            
            # 根据持仓方向和偏度差值决定是否平仓
            if self.position_type == 'long_j_short_jm' and (current_delta > self.lower_exit_threshold or days_in_trade >= self.p.max_hold_days):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(f'平仓: J-JM偏度差={current_delta:.2f}, 持仓天数={days_in_trade}, 平仓阈值={self.lower_exit_threshold:.2f}')
            
            elif self.position_type == 'short_j_long_jm' and (current_delta < self.upper_exit_threshold or days_in_trade >= self.p.max_hold_days):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(f'平仓: J-JM偏度差={current_delta:.2f}, 持仓天数={days_in_trade}, 平仓阈值={self.upper_exit_threshold:.2f}')
                
        else:
            # 开仓逻辑
            if current_delta > self.upper_entry_threshold:
                # J的偏度显著高于历史均值，做空J，做多JM
                self.order = self.sell(data=self.data0, size=10)
                self.order = self.buy(data=self.data1, size=14)
                self.entry_day = len(self)
                self.position_type = 'short_j_long_jm'
                if self.p.printlog:
                    print(f'开仓: 做空J，做多JM, 偏度差={current_delta:.2f}, 开仓阈值={self.upper_entry_threshold:.2f}')
                
            elif current_delta < self.lower_entry_threshold:
                # J的偏度显著低于历史均值，做多J，做空JM
                self.order = self.buy(data=self.data0, size=10)
                self.order = self.sell(data=self.data1, size=14)
                self.entry_day = len(self)
                self.position_type = 'long_j_short_jm'
                if self.p.printlog:
                    print(f'开仓: 做多J，做空JM, 偏度差={current_delta:.2f}, 开仓阈值={self.lower_entry_threshold:.2f}')

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

    # def notify_trade(self, trade):
    #     if self.p.printlog and trade.isclosed:
    #         print(f'平仓盈利: {trade.pnlcomm:.2f}')
            
    # def stop(self):
    #     # 策略结束时绘制偏度图形
    #     if len(self.skew_j_values) > 0:
    #         self.plot_skewness()
    
    def plot_skewness(self):
        # 创建日期索引
        if len(self.dates) > len(self.skew_j_values):
            dates = self.dates[-(len(self.skew_j_values)):]
        else:
            dates = self.dates
        
        # 创建一个新的图形
        plt.figure(figsize=(12, 10))
        
        # 绘制J和JM的偏度
        plt.subplot(3, 1, 1)
        plt.plot(dates, self.skew_j_values, label='J Skewness', color='blue')
        plt.plot(dates, self.skew_jm_values, label='JM Skewness', color='red')
        plt.title('Skewness of J and JM Contracts')
        plt.legend()
        plt.grid(True)
        
        # 绘制偏度差值
        plt.subplot(3, 1, 2)
        plt.plot(dates, self.delta_skew_values, label='Skewness Difference (J-JM)', color='green')
        
        # 只绘制最后一个交易日的阈值线
        if len(self.delta_skew_values) > 0:
            plt.axhline(y=self.upper_entry_threshold, color='r', linestyle='--', 
                       label=f'Upper Entry Threshold (Mean + {self.p.entry_std_multiplier}σ)')
            plt.axhline(y=self.lower_entry_threshold, color='r', linestyle='--', 
                       label=f'Lower Entry Threshold (Mean - {self.p.entry_std_multiplier}σ)')
            plt.axhline(y=self.upper_exit_threshold, color='g', linestyle=':', 
                       label=f'Upper Exit Threshold (Mean + {self.p.exit_std_multiplier}σ)')
            plt.axhline(y=self.lower_exit_threshold, color='g', linestyle=':', 
                       label=f'Lower Exit Threshold (Mean - {self.p.exit_std_multiplier}σ)')
            plt.axhline(y=self.delta_mean, color='k', linestyle='-', 
                       label='Mean')
        
        plt.title('Skewness Difference (J-JM) with Dynamic Thresholds')
        plt.legend()
        plt.grid(True)
        
        # 绘制价格
        plt.subplot(3, 1, 3)
        plt.plot(dates, [self.data0.close[i] for i in range(-len(dates), 0)], label='J Price', color='blue')
        plt.plot(dates, [self.data1.close[i] for i in range(-len(dates), 0)], label='JM Price', color='red')
        plt.title('Price of J and JM Contracts')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()

        plt.show()
        print("偏度图表已保存为 'skewness_plot.png'")


# 关键修复：处理索引问题
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
    skew_periods = range(10, 41, 5)  # 10, 15, 20, 25, 30, 35, 40
    entry_multipliers = [0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0]
    
    # 存储结果
    results = np.zeros((len(skew_periods), len(entry_multipliers)))
    
    # 设置初始日期
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)
    
    # 加载数据一次（这些数据可以重复使用）
    data0, data1 = load_data('/J', '/JM', fromdate, todate)
    
    if data0 is None or data1 is None:
        print("无法加载数据，请检查文件路径和数据格式")
        return
    
    print("开始网格回测...")
    print(f"测试参数组合: {len(skew_periods)} x {len(entry_multipliers)} = {len(skew_periods) * len(entry_multipliers)}个组合")
    
    # 进行网格回测
    for i, skew_period in enumerate(skew_periods):
        for j, entry_multiplier in enumerate(entry_multipliers):
            print(f"测试参数: skew_period={skew_period}, entry_std_multiplier={entry_multiplier}")
            
            # 创建一个新的cerebro实例
            cerebro = bt.Cerebro(stdstats=False)
            
            # 添加相同的数据
            cerebro.adddata(data0, name='J')
            cerebro.adddata(data1, name='JM')
            
            # 添加策略，使用当前测试的参数
            cerebro.addstrategy(SkewnessArbitrageStrategy, 
                                skew_period=skew_period, 
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
            
            # 获取夏普比率
            sharpe = strats[0].analyzers.sharperatio.get_analysis().get('sharperatio', 0)
            
            # 存储结果
            results[i, j] = sharpe
            
            print(f"夏普比率: {sharpe:.2f}")
    
    # 绘制热力图
    plt.figure(figsize=(12, 8))
    
    # 使用Seaborn的热力图
    ax = sns.heatmap(results, 
                     annot=True, 
                     fmt=".2f", 
                     cmap="YlGnBu", 
                     xticklabels=entry_multipliers, 
                     yticklabels=skew_periods)
    
    # 设置标题和标签
    plt.title('sharperatio - skew_period vs entry_std_multiplier')
    plt.xlabel('entry_std_multiplier')
    plt.ylabel('skew_period')
    
    # 显示图形
    plt.tight_layout()
    plt.savefig('sharpe_ratio_heatmap.png')
    plt.show()
    
    print("热力图已保存为 'sharpe_ratio_heatmap.png'")
    
    # 找出最佳参数组合
    max_i, max_j = np.unravel_index(results.argmax(), results.shape)
    best_skew_period = skew_periods[max_i]
    best_entry_multiplier = entry_multipliers[max_j]
    best_sharpe = results[max_i, max_j]
    
    print(f"\n最佳参数组合:")
    print(f"skew_period: {best_skew_period}")
    print(f"entry_std_multiplier: {best_entry_multiplier}")
    print(f"sharperatio: {best_sharpe:.4f}")
    
    return results, skew_periods, entry_multipliers

# 修改主函数，调用网格搜索
if __name__ == '__main__':
    run_grid_search() 