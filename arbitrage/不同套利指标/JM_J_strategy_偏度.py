import backtrader as bt
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import seaborn as sns


# 偏度差均值回归策略（基于历史统计量的版本）
class SkewnessArbitrageStrategy(bt.Strategy):
    params = (
        ('skew_period', 10),       # 计算偏度的周期
        ('lookback_period', 60),   # 计算历史统计量的回看周期
        ('entry_std_multiplier', 2),  # 开仓标准差乘数
        ('exit_std_multiplier', 0.3),   # 平仓标准差乘数
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
        print(self.position_type)
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

    def notify_trade(self, trade):
        if self.p.printlog and trade.isclosed:
            print(f'平仓盈利: {trade.pnlcomm:.2f}')
            
    def stop(self):
        # 策略结束时绘制偏度图形
        if len(self.skew_j_values) > 0:
            self.plot_skewness()
    
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
        plt.savefig('skewness_plot.png')
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

# 其余代码保持不变
def configure_cerebro(**kwargs):
    cerebro = bt.Cerebro(stdstats=False)  # 启用标准统计
    data0, data1 = load_data('/J', '/JM', datetime.datetime(2017, 1, 1), datetime.datetime(2025, 1, 1))
    
    if data0 is None or data1 is None:
        print("无法加载数据，请检查文件路径和数据格式")
        return None
        
    cerebro.adddata(data0, name='J')
    cerebro.adddata(data1, name='JM')
    cerebro.addstrategy(SkewnessArbitrageStrategy, printlog=True)  # 启用日志输出
    cerebro.broker.setcash(80000)
    # cerebro.broker.setcommission(0.0003)
    cerebro.broker.set_shortcash(False)

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
    cerebro.addanalyzer(bt.analyzers.CAGRAnalyzer, period=bt.TimeFrame.Days,plot=True)  # 这里的period可以是daily, weekly, monthly等
    # cerebro.broker.setcommission(commission=0.001)
    cerebro.broker.set_shortcash(False)
    # cerebro.addobserver(bt.observers.Trades)
    # # cerebro.addobserver(bt.observers.BuySell)
    # cerebro.addobserver(bt.observers.CumValue)
    return cerebro

def analyze_results(results):
    if not results:
        print("没有回测结果可分析")
        return
        
    try:
        # 获取分析结果
        drawdown = results[0].analyzers.drawdown.get_analysis()
        sharpe = results[0].analyzers.sharperatio.get_analysis()
        roi = results[0].analyzers.roianalyzer.get_analysis()
        total_returns = results[0].analyzers.returns.get_analysis()  # 获取总回报率
        cagr = results[0].analyzers.cagranalyzer.get_analysis()
        # # 打印分析结果
        print("=============回测结果================")
        print(f"\nSharpe Ratio: {sharpe.get('sharperatio', 0):.2f}")
        print(f"Drawdown: {drawdown.get('max', {}).get('drawdown', 0):.2f} %")
        print(f"Annualized/Normalized return: {total_returns.get('rnorm100', 0):.2f}%")  #
        print(f"Total compound return: {roi.get('roi100', 0):.2f}%")
        print(f"年化收益: {cagr.get('cagr', 0):.2f} ")
        print(f"夏普比率: {cagr.get('sharpe', 0):.2f}")
    except Exception as e:
        print(f"分析结果时出错: {e}")



if __name__ == '__main__':
    cerebro = configure_cerebro()
    if cerebro:
        print("开始回测...")
        results = cerebro.run()
        analyze_results(results)
        print("绘制结果...")
        
