import backtrader as bt
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from arbitrage.myutil import calculate_spread  # 假设这是您的价差计算函数

# 布林带价差交易策略（参数已优化为可通过网格搜索调整）
class SpreadBollingerStrategy(bt.Strategy):
    params = (
        ('period', 15),        # 布林带周期（可调参数）
        ('devfactor', 1.5),    # 标准差倍数（可调参数）
        ('size0', 10),         # 品种0交易手数（可调参数）
        ('size1', 14),         # 品种1交易手数（可调参数）
        ('printlog', False),   # 是否打印交易日志
    )

    def __init__(self):
        # 布林带指标（使用价差序列）
        self.boll = bt.indicators.BollingerBands(
            self.data2.close,
            period=self.p.period,
            devfactor=self.p.devfactor,
            subplot=False
        )
        
        # 交易状态跟踪
        self.order = None
        self.entry_price = 0
        self.position_size = 0

    def next(self):
        if self.order:  # 存在未完成订单时跳过
            return

        spread = self.data2.close[0]
        mid = self.boll.lines.mid[0]
        pos = self.getposition(self.data0).size

        # 开仓逻辑
        if pos == 0:
            if spread > self.boll.lines.top[0]:
                self._execute_trade('short')
            elif spread < self.boll.lines.bot[0]:
                self._execute_trade('long')
        
        # 平仓逻辑
        else:
            if (spread <= mid and pos < 0) or (spread >= mid and pos > 0):
                self._close_positions()

    def _execute_trade(self, direction):
        """执行开仓操作"""
        self.entry_price = self.data2.close[0]
        if direction == 'short':
            self.sell(data=self.data0, size=self.p.size0)
            self.buy(data=self.data1, size=self.p.size1)
        else:
            self.buy(data=self.data0, size=self.p.size0)
            self.sell(data=self.data1, size=self.p.size1)

    def _close_positions(self):
        """执行平仓操作"""
        self.close(data=self.data0)
        self.close(data=self.data1)

    def notify_trade(self, trade):
        """可选：交易通知记录"""
        if self.p.printlog:
            if trade.isclosed:
                print(f'{trade.ref} 平仓 | 盈利 {trade.pnlcomm:.2f}')
            elif trade.justopened:
                print(f'{trade.ref} 开仓 | 数量 {trade.size}')

# 数据加载函数（与策略解耦）
def load_data(symbol1, symbol2, fromdate, todate):
    """加载数据并计算价差"""
    output_file = 'D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5'
    
    # 加载原始数据
    df0 = pd.read_hdf(output_file, key=symbol1).reset_index()
    df1 = pd.read_hdf(output_file, key=symbol2).reset_index()
    
    # 计算价差（此处参数可根据需要调整）
    df_spread = calculate_spread(df0, df1, 1, 1.4)
    
    # 创建数据feed
    data0 = bt.feeds.PandasData(dataname=df0, datetime='date', 
                              fromdate=fromdate, todate=todate)
    data1 = bt.feeds.PandasData(dataname=df1, datetime='date',
                              fromdate=fromdate, todate=todate)
    data2 = bt.feeds.PandasData(dataname=df_spread, datetime='date',
                              fromdate=fromdate, todate=todate)
    return data0, data1, data2

# 回测配置函数
def configure_cerebro(**kwargs):
    """配置回测引擎"""
    cerebro = bt.Cerebro(stdstats=False)
    
    # 添加数据
    data0, data1, data2 = load_data(
        symbol1='/J', 
        symbol2='/JM',
        fromdate=datetime.datetime(2017, 1, 1),
        todate=datetime.datetime(2025, 1, 1)
    )
    
    cerebro.adddata(data0, name='data0')
    cerebro.adddata(data1, name='data1')
    cerebro.adddata(data2, name='spread')

    # 添加策略（使用optstrategy进行参数优化）
    cerebro.optstrategy(
        SpreadBollingerStrategy,
        period=range(10, 25, 5),       # 测试周期参数：10,15,20
        devfactor=[1.0, 1.5, 2.0],     # 标准差倍数参数
        printlog=False                 # 关闭详细日志
    )

    # 设置资金和手续费
    cerebro.broker.setcash(80000)
    # cerebro.broker.setcommission(commission=0.0003)
    cerebro.broker.set_shortcash(False)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, 
                      timeframe=bt.TimeFrame.Days, 
                      riskfreerate=0.0, 
                      annualize=True, 
                      _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, 
                      tann=bt.TimeFrame.Days, 
                      _name='returns')
    return cerebro


# 修改后的分析函数
def analyze_results(results):
    """分析优化结果并输出最佳参数组合"""
    performance = []
    
    # 遍历所有参数组合的回测结果
    for strat_list in results:
        strat = strat_list[0]  # 获取策略实例
        params = strat.params  # 当前参数组合
        
        # 获取分析指标
        dd = strat.analyzers.drawdown.get_analysis()
        sharpe = strat.analyzers.sharpe.get_analysis()
        returns = strat.analyzers.returns.get_analysis()
        
        # 存储性能指标
        performance.append({
            'period': params.period,
            'devfactor': params.devfactor,
            'sharpe': sharpe['sharperatio'],
            'max_dd': dd['max']['drawdown'],
            'return': returns['rnorm100']
        })

    # 创建DataFrame
    df = pd.DataFrame(performance)
    
    # 生成热力图数据
    heatmap_data = df.pivot_table(index='period', 
                                columns='devfactor', 
                                values='sharpe', 
                                aggfunc='mean')
    
    # 绘制热力图
    plt.figure(figsize=(10, 6))
    sns.heatmap(heatmap_data, 
                annot=True, 
                fmt=".2f",
                cmap="RdYlGn",
                cbar_kws={'label': '夏普比率'})
    plt.title("参数组合夏普比率热力图")
    plt.xlabel("标准差倍数 (devfactor)")
    plt.ylabel("布林带周期 (period)")
    plt.tight_layout()
    plt.show()

    # 按夏普比率排序
    sorted_perf = sorted(performance, key=lambda x: x['sharpe'], reverse=True)
    
    # 输出前5最佳组合
    print("\n=========== 最佳参数组合 ===========")
    for i, result in enumerate(sorted_perf[:5]):
        print(f"\n组合 {i+1}:")
        print(f"参数: {result['params']}")
        print(f"夏普比率: {result['sharpe']:.2f}")
        print(f"最大回撤: {result['max_dd']:.2f}%")
        print(f"年化收益: {result['return']:.2f}%")

# 主执行函数
if __name__ == '__main__':
    cerebro = configure_cerebro()
    results = cerebro.run()
    analyze_results(results)
    # cerebro.plot()  # 需要查看具体回测时可取消注释