import backtrader as bt
import pandas as pd
import numpy as np
import datetime

class RSIArbitrageStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),        # RSI周期
        ('rsi_overbought', 70),    # RSI超买阈值
        ('rsi_oversold', 30),      # RSI超卖阈值
        ('printlog', False),
    )

    def __init__(self):
        # 计算价差
        self.price_diff = self.data0.close - 1.4*self.data1.close
        
        # 使用价差序列计算RSI
        self.price_diff_rsi = bt.indicators.RSI(self.price_diff, period=self.p.rsi_period)
        
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
                self.price_diff_rsi[0] >= self.p.rsi_overbought):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(f'平仓: 价差={self.price_diff[0]:.2f}, 价差RSI={self.price_diff_rsi[0]:.2f}')
            
            elif (self.position_type == 'short_j_long_jm' and 
                  self.price_diff_rsi[0] <= self.p.rsi_oversold):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(f'平仓: 价差={self.price_diff[0]:.2f}, 价差RSI={self.price_diff_rsi[0]:.2f}')
                
        else:
            # 开仓条件
            if self.price_diff_rsi[0] >= self.p.rsi_overbought:
                # 做空J，做多JM
                self.order = self.sell(data=self.data0, size=10)
                self.order = self.buy(data=self.data1, size=14)
                self.position_type = 'short_j_long_jm'
                if self.p.printlog:
                    print(f'开仓: 做空J，做多JM, 价差={self.price_diff[0]:.2f}, 价差RSI={self.price_diff_rsi[0]:.2f}')
                
            elif self.price_diff_rsi[0] <= self.p.rsi_oversold:
                # 做多J，做空JM
                self.order = self.buy(data=self.data0, size=10)
                self.order = self.sell(data=self.data1, size=14)
                self.position_type = 'long_j_short_jm'
                if self.p.printlog:
                    print(f'开仓: 做多J，做空JM, 价差={self.price_diff[0]:.2f}, 价差RSI={self.price_diff_rsi[0]:.2f}')

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

def run_strategy():
    # 创建回测引擎
    cerebro = bt.Cerebro()
    
    # 设置初始资金
    cerebro.broker.setcash(100000)
    
    # 设置滑点
    cerebro.broker.set_slippage_perc(perc=0.0005)  # 设置0.1%的滑点
    
    # 设置手续费
    # cerebro.broker.setcommission(commission=0.0003)
    
    cerebro.broker.set_shortcash(False)
    
    # 加载数据
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)
    data0, data1 = load_data('/J', '/JM', fromdate, todate)
    
    if data0 is None or data1 is None:
        print("无法加载数据，请检查文件路径和数据格式")
        return
    
    # 添加数据
    cerebro.adddata(data0, name='J')
    cerebro.adddata(data1, name='JM')
    
    # 添加策略
    cerebro.addstrategy(RSIArbitrageStrategy, printlog=True)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # 运行回测
    print('初始资金: %.2f' % cerebro.broker.getvalue())
    results = cerebro.run()
    print('最终资金: %.2f' % cerebro.broker.getvalue())
    
    # 打印分析结果
    strat = results[0]
    print('夏普比率:', strat.analyzers.sharpe_ratio.get_analysis()['sharperatio'])
    print('最大回撤:', strat.analyzers.drawdown.get_analysis()['max']['drawdown'])
    print('年化收益率:', strat.analyzers.returns.get_analysis()['rnorm100'])
    
    # 使用backtrader原生绘图
    # cerebro.plot()

if __name__ == '__main__':
    run_strategy() 