import backtrader as bt
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from itertools import product
import itertools
import seaborn as sns

class HurstBollingerStrategy(bt.Strategy):
    params = (
        ('hurst_period', 20),      # Hurst指数计算周期
        ('bollinger_period', 7),  # 布林带周期
        ('bollinger_dev', 1.5),    # 布林带标准差倍数
        ('printlog', False),
    )

    def __init__(self):
        # 计算价差
        self.price_diff = self.data0.close - 1.4*self.data1.close
        
        # 计算布林带
        self.bollinger = bt.indicators.BollingerBands(
            self.price_diff,
            period=self.p.bollinger_period,
            devfactor=self.p.bollinger_dev
        )
        
        # 计算Hurst指数
        self.hurst = bt.indicators.Hurst(
            self.price_diff,
            period=self.p.hurst_period
        )
        
        # 交易相关变量
        self.order = None
        self.position_type = None

    def next(self):
        if self.order:
            return
            
        # 交易逻辑
        if self.position:
            # 平仓条件
            if (self.position_type == 'long_j_short_jm' and 
                self.price_diff[0] >= self.bollinger.mid[0]):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(f'平仓: 价差={self.price_diff[0]:.2f}, Hurst={self.hurst[0]:.2f}')
            
            elif (self.position_type == 'short_j_long_jm' and 
                  self.price_diff[0] <= self.bollinger.mid[0]):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(f'平仓: 价差={self.price_diff[0]:.2f}, Hurst={self.hurst[0]:.2f}')
                
        else:
            # 开仓条件：Hurst指数小于0.5（均值回归）且价差突破布林带
            if (self.hurst[0] > 0.5 and 
                self.price_diff[0] >= self.bollinger.top[0]):
                # 做空J，做多JM
                self.order = self.buy(data=self.data0, size=10)
                self.order = self.sell(data=self.data1, size=14)
                self.position_type = 'short_j_long_jm'
                if self.p.printlog:
                    print(f'开仓: ,做空J，做多JM, 价差={self.price_diff[0]:.2f}, Hurst={self.hurst[0]:.2f}')
                
            elif (self.hurst[0] > 0.5 and 
                  self.price_diff[0] <= self.bollinger.bot[0]):
                # 做多J，做空JM
                self.order = self.sell(data=self.data0, size=10)
                self.order = self.buy(data=self.data1, size=14)
                self.position_type = 'long_j_short_jm'
                if self.p.printlog:
                    print(f'开仓: 做多J，做空JM, 价差={self.price_diff[0]:.2f}, Hurst={self.hurst[0]:.2f}')

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

def load_data(symbol1, symbol2, fromdate, todate):
    output_file = 'D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5'
    
    try:
        df0 = pd.read_hdf(output_file, key=symbol1).reset_index()
        df1 = pd.read_hdf(output_file, key=symbol2).reset_index()
        
        date_col = [col for col in df0.columns if 'date' in col.lower()]
        if not date_col:
            raise ValueError("数据集中未找到日期列")
        
        df0 = df0.set_index(pd.to_datetime(df0[date_col[0]]))
        df1 = df1.set_index(pd.to_datetime(df1[date_col[0]]))
        df0 = df0.sort_index().loc[fromdate:todate]
        df1 = df1.sort_index().loc[fromdate:todate]
        
        data0 = bt.feeds.PandasData(
            dataname=df0,
            datetime=None,
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

def optimize_parameters():
    # 定义参数范围
    hurst_periods = [10, 15, 20, 25, 30]
    bollinger_periods = [5, 7, 10, 14, 20]
    bollinger_devs = [1.0, 1.5, 2.0, 2.5, 3.0]
    
    results = []
    best_sharpe = -float('inf')
    best_params = None
    
    # 遍历所有参数组合
    for hurst, period, dev in itertools.product(hurst_periods, bollinger_periods, bollinger_devs):
        print(f'参数组合: Hurst={hurst}, Bollinger周期={period}, 标准差倍数={dev}')
        
        # 运行回测
        result = run_strategy(hurst_period=hurst, bollinger_period=period, bollinger_dev=dev)
        
        if result is None:
            print('回测失败')
            continue
        
        # 获取回测结果
        sharpe = result['sharpe']
        drawdown = result['drawdown']
        returns = result['returns']
        
        # 处理None值
        sharpe_str = f'{sharpe:.4f}' if sharpe is not None else 'N/A'
        drawdown_str = f'{drawdown:.2f}%' if drawdown is not None else 'N/A'
        returns_str = f'{returns:.2f}%' if returns is not None else 'N/A'
        
        print(f'夏普比率: {sharpe_str}, 最大回撤: {drawdown_str}, 年化收益: {returns_str}')
        print('-' * 50)
        
        # 只记录有效的回测结果
        if sharpe is not None:
            results.append({
                'hurst': hurst,
                'period': period,
                'dev': dev,
                'sharpe': sharpe,
                'drawdown': drawdown,
                'returns': returns
            })
            
            # 更新最佳参数
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_params = (hurst, period, dev)
    
    # 打印最佳参数
    if best_params:
        print(f'\n最佳参数组合:')
        print(f'Hurst周期: {best_params[0]}')
        print(f'布林带周期: {best_params[1]}')
        print(f'标准差倍数: {best_params[2]}')
        print(f'夏普比率: {best_sharpe:.4f}')
    
    # 绘制热力图
    plot_heatmap(results)

def plot_heatmap(results):
    if not results:
        print('没有有效的回测结果，无法绘制热力图')
        return
        
    # 将结果列表转换为DataFrame
    results_df = pd.DataFrame(results)
    
    # 为每个标准差倍数创建一个热力图
    unique_devs = sorted(results_df['dev'].unique())
    
    # 创建子图
    fig, axes = plt.subplots(1, len(unique_devs), figsize=(20, 5))
    if len(unique_devs) == 1:
        axes = [axes]
    
    for i, dev in enumerate(unique_devs):
        # 筛选当前标准差倍数的数据
        dev_data = results_df[results_df['dev'] == dev]
        
        # 创建热力图数据
        heatmap_data = dev_data.pivot_table(
            index='hurst',
            columns='period',
            values='sharpe'
        )
        
        # 绘制热力图
        sns.heatmap(heatmap_data, 
                   annot=True, 
                   fmt='.2f',
                   cmap='RdYlGn',
                   center=0,
                   ax=axes[i])
        
        axes[i].set_title(f'标准差倍数 = {dev}')
        axes[i].set_xlabel('布林带周期')
        axes[i].set_ylabel('Hurst周期')
    
    plt.tight_layout()
    plt.savefig('hurst_bollinger_heatmap.png')
    plt.close()
    
    print('热力图已保存为 hurst_bollinger_heatmap.png')

def run_strategy(hurst_period, bollinger_period, bollinger_dev, plot=False):
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(150000)
    cerebro.broker.set_slippage_perc(perc=0.0005)
    cerebro.broker.set_shortcash(False)
    
    # 加载数据
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)
    data0, data1 = load_data('/J', '/JM', fromdate, todate)
    
    if data0 is None or data1 is None:
        print("无法加载数据，请检查文件路径和数据格式")
        return None
        
    cerebro.adddata(data0, name='J')
    cerebro.adddata(data1, name='JM')
    
    # 添加策略
    cerebro.addstrategy(HurstBollingerStrategy, 
                       hurst_period=hurst_period,
                       bollinger_period=bollinger_period,
                       bollinger_dev=bollinger_dev,
                       printlog=False)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                       timeframe=bt.TimeFrame.Days,
                       riskfreerate=0,
                       annualize=True,
                       _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # 运行回测
    results = cerebro.run()
    
    result_dict = {'sharpe': None, 'drawdown': None, 'returns': None}
    
    if results and len(results) > 0:
        result = results[0]
        # 获取分析结果
        result_dict['sharpe'] = result.analyzers.sharpe_ratio.get_analysis().get('sharperatio', None)
        result_dict['drawdown'] = result.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', None)
        result_dict['returns'] = result.analyzers.returns.get_analysis().get('rnorm100', None)
    
    if plot:
        cerebro.plot()
    
    return result_dict

if __name__ == '__main__':
    # 运行参数优化
    optimize_parameters()
    
    # 运行单次回测（使用最优参数）
    # run_strategy() 