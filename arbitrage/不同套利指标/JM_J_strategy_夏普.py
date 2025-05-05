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

        if self.position:
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

    def notify_trade(self, trade):
        if self.p.printlog and trade.isclosed:
            print(f'平仓盈利: {trade.pnlcomm:.2f}')
            
    def stop(self):
        # 策略结束时绘制夏普比率图形
        if len(self.delta_sharpe_values) > 0:
            self.plot_sharpe_ratio()
    
    def plot_sharpe_ratio(self):
        # 创建绘图的数据索引
        if len(self.delta_sharpe_ma) > 0:  # 确保有布林带数据
            # 使用有布林带数据的时间段
            band_length = len(self.delta_sharpe_ma)
            dates = self.dates[-band_length:]
            delta_values = self.delta_sharpe_values[-band_length:]
            sharpe_j = self.sharpe_j_values[-band_length:]
            sharpe_jm = self.sharpe_jm_values[-band_length:]
            
            # 创建一个新的图形
            plt.figure(figsize=(12, 10))
            
            # 绘制J和JM的夏普比率
            plt.subplot(3, 1, 1)
            plt.plot(dates, sharpe_j, label='J Sharpe Ratio', color='blue')
            plt.plot(dates, sharpe_jm, label='JM Sharpe Ratio', color='red')
            plt.title('Sharpe Ratio of J and JM Contracts (15-day)')
            plt.legend()
            plt.grid(True)
            
            # 绘制夏普差值和布林带
            plt.subplot(3, 1, 2)
            plt.plot(dates, delta_values, label='Sharpe Difference (J-JM)', color='green')
            plt.plot(dates, self.delta_sharpe_ma, label='20-day MA', color='black')
            plt.plot(dates, self.upper_band, label=f'Upper Band (MA + {self.p.entry_std_multiplier}σ)', color='red', linestyle='--')
            plt.plot(dates, self.lower_band, label=f'Lower Band (MA - {self.p.entry_std_multiplier}σ)', color='red', linestyle='--')
            
            plt.title('Sharpe Ratio Difference (J-JM) with Bollinger Bands')
            plt.legend()
            plt.grid(True)
            
            # 绘制价格
            plt.subplot(3, 1, 3)
            plt.plot(dates, [self.j_prices[-(i+1)] for i in range(len(dates)-1, -1, -1)], label='J Price', color='blue')
            plt.plot(dates, [self.jm_prices[-(i+1)] for i in range(len(dates)-1, -1, -1)], label='JM Price', color='red')
            plt.title('Price of J and JM Contracts')
            plt.legend()
            plt.grid(True)
            
            plt.tight_layout()
            plt.savefig('sharpe_ratio_plot.png')
            plt.show()
            print("夏普比率图表已保存为 'sharpe_ratio_plot.png'")


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

# 配置回测引擎
def configure_cerebro(**kwargs):
    cerebro = bt.Cerebro(stdstats=False)  # 启用标准统计
    data0, data1 = load_data('/J', '/JM', datetime.datetime(2017, 1, 1), datetime.datetime(2025, 1, 1))
    
    if data0 is None or data1 is None:
        print("无法加载数据，请检查文件路径和数据格式")
        return None
        
    cerebro.adddata(data0, name='J')
    cerebro.adddata(data1, name='JM')
    cerebro.addstrategy(SharpeDiffStrategy, printlog=True)  # 启用日志输出
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
        cerebro.plot()