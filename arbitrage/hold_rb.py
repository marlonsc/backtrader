import backtrader as bt
import pandas as pd
from myutil import calculate_spread, check_and_align_data

# 始终持有螺纹钢策略
class AlwaysHoldRBStrategy(bt.Strategy):
    params = (
        ('size_rb', 1),  # 螺纹钢交易规模
    )
    
    def __init__(self):

        self.order = None
        
    def next(self):
        # 始终持有螺纹钢，不做任何交易

        if not self.position:  # 如果没有持仓，则买入
            self.order = self.buy(data=self.data0, size=self.p.size_rb, price=self.data0.close[0])  # 买1手螺纹钢
            print(f"下单价格: {self.data0.close[0]}, 时间: {self.data0.datetime.datetime()}, 持仓: {self.position}")

    
    def notify_order(self, order):
        # 订单状态通知      
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None


# 读取数据
output_file = 'D://y5//RB_daily.h5'
df_RB = pd.read_hdf(output_file, key='data')

# 确保 'date' 列转换为 datetime 类型
df_RB['date'] = pd.to_datetime(df_RB['date'], errors='coerce')


data1 = bt.feeds.PandasData(dataname=df_RB, datetime='date', nocase=True)

# 创建回测引擎
cerebro = bt.Cerebro()

cerebro.adddata(data1, name='RB')


# 添加策略
cerebro.addstrategy(AlwaysHoldRBStrategy)

# 设置初始资金
# cerebro.broker.setcash(1000000.0)

# 添加分析器：SharpeRatio、DrawDown、AnnualReturn 和 Returns
cerebro.addanalyzer(bt.analyzers.SharpeRatio, 
                    timeframe=bt.TimeFrame.Days,  # 按日数据计算
                    riskfreerate=0,            # 默认年化1%的风险无风险利率
                    annualize=True,           # 不进行年化


                    ) 
cerebro.addanalyzer(bt.analyzers.AnnualReturn)      
cerebro.addanalyzer(bt.analyzers.DrawDown)  # 回撤分析器
cerebro.addanalyzer(bt.analyzers.Returns,
                    # timeframe=bt.TimeFrame.Days,  # 按日数据计算
                    tann=bt.TimeFrame.Days,  # 年化因子，252 个交易日
                    )  # 自定义名称

# 添加CAGR分析器
cerebro.addanalyzer(bt.analyzers.CAGRAnalyzer, period=bt.TimeFrame.Days)  # 这里的period可以是daily, weekly, monthly等
# 运行回测
results = cerebro.run()

# 获取分析结果
sharpe = results[0].analyzers.sharperatio.get_analysis()
drawdown = results[0].analyzers.drawdown.get_analysis()
annual_returns = results[0].analyzers.annualreturn.get_analysis()
total_returns = results[0].analyzers.returns.get_analysis()  # 获取总回报率
cagr = results[0].analyzers.cagranalyzer.get_analysis()
print(cagr)
# 打印分析结果
print(f"\n夏普比率: {sharpe['sharperatio']}")
print(f"最大回撤: {drawdown['max']['drawdown']} %")
print(f"总回报率: {total_returns['rnorm100']:.2f}%")  # 打印总回报率

# 打印年度回报率
print("\n年度回报率:")
print("=" * 80)
print("{:<8} {:<12}".format("年份", "回报率"))
for year, return_rate in annual_returns.items():
    print("{:<8} {:<12.2%}".format(year, return_rate))

# 绘制结果
# cerebro.plot(volume=False)
