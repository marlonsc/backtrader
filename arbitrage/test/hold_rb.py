import pandas as pd

import backtrader as bt



# 设置显示选项，不使用省略号
pd.set_option('display.max_columns', None)  # 显示所有列
pd.set_option('display.max_colwidth', None)  # 显示列的完整内容

# 始终持有螺纹钢策略
class AlwaysHoldRBStrategy(bt.Strategy):
    params = (
        ('size_rb', 1),  # 螺纹钢交易规模
    )
    def __init__(self):

        self.order = None
    def start(self):
        # Activate the fund mode and set the default value at 100
        # self.broker.set_fundmode(fundmode=True, fundstartval=100.00)
        self.cash_start = self.broker.get_cash()
        # self.val_start = 100.0
    def next(self):

        if not self.position:  # 如果没有持仓，则买入
            self.order = self.buy(data=self.data0, size=self.p.size_rb, price=self.data0.close[0])  # 买1手螺纹钢
        # print(self.broker.get_fundvalue(),self.broker.get_value(),self.position,self.order)
        # print(self.data.datetime[1],self.data.datetime[0],self.data.datetime[-1]   )
        if self.data.datetime[0] == 739257.0 :  # 最后一天的判断

            self.close(exectype = self.order.Close)

            # print(f"下单价格: {self.data0.close[0]}, 时间: {self.data0.datetime.datetime()}, 持仓: {self.position}")

    def stop(self):
        # calculate the actual returns
        self.roi = (self.broker.get_value() - self.cash_start) - 1.0
        # self.froi = self.broker.get_fundvalue() - self.val_start
        print('ROI:   {:.2f}%'.format(self.roi))
        # print('Fund Value: {:.2f}%'.format(self.froi))
    def notify_trade(self, trade):
        if trade.isclosed:
            print('TRADE CLOSED %s, PROFIT: GROSS %.2f, NET %.2f' %
                     (bt.num2date(trade.dtclose),trade.pnl, trade.pnlcomm))

        elif trade.justopened:
            print('TRADE OPENED %s  , SIZE %2d' % (bt.num2date(trade.dtopen),trade.size))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单状态 submitted/accepted，处于未决订单状态。
            return

        # 订单已决，执行如下语句
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'executed date {bt.num2date(order.executed.dt)},executed price {order.executed.price}, created date {bt.num2date(order.created.dt)}')

# 读取数据
output_file = 'D://y5//RB_daily.h5'
df_RB = pd.read_hdf(output_file, key='data')

# 确保 'date' 列转换为 datetime 类型
df_RB['date'] = pd.to_datetime(df_RB['date'], errors='coerce')

# 检查数据头部
print(df_RB.head())


data1 = bt.feeds.PandasData(dataname=df_RB, datetime='date', nocase=True)

# 创建回测引擎
cerebro = bt.Cerebro()

cerebro.adddata(data1, name='RB')

# 添加策略
cerebro.addstrategy(AlwaysHoldRBStrategy)

# 设置初始资金
cerebro.broker.setcash(1000.0)
cerebro.broker.set_shortcash(False)
# 添加分析器：SharpeRatio、DrawDown、AnnualReturn 和 Returns
cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                    timeframe=bt.TimeFrame.Days,  # 按日数据计算
                    riskfreerate=0,            # 默认年化1%的风险无风险利率
                    annualize=True,           # 不进行年化

                    )
cerebro.addanalyzer(bt.analyzers.AnnualReturn)
cerebro.addanalyzer(bt.analyzers.DrawDown)  # 回撤分析器
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)  # 回撤分析器
# cerebro.addanalyzer(bt.analyzers.Returns,
#                     tann=bt.TimeFrame.Days,  # 年化因子，252 个交易日
#                     )  # 自定义名称

cerebro.addanalyzer(bt.analyzers.CAGRAnalyzer, period=bt.TimeFrame.Days)  # 这里的period可以是daily, weekly, monthly等
# 运行回测
results = cerebro.run()

# 获取分析结果
sharpe = results[0].analyzers.sharperatio.get_analysis()
drawdown = results[0].analyzers.drawdown.get_analysis()
# annual_returns = results[0].analyzers.annualreturn.get_analysis()
# total_returns = results[0].analyzers.returns.get_analysis()  # 获取总回报率
cagr = results[0].analyzers.cagranalyzer.get_analysis()
trade = results[0].analyzers.tradeanalyzer.get_analysis()

# 打印分析结果
print("=============回测结果================")
print(f"\n夏普比率: {sharpe['sharperatio']:.2f}")
print(f"最大回撤: {drawdown['max']['drawdown']:.2f} %")
# print(f"总回报率: {total_returns['rnorm100']:.2f}%")  # 打印总回报率
print(f"年化收益: {cagr['cagr']:.2f} %")
print(f"sharpe: {cagr['sharpe']:.2f} ")

print(f"交易记录: {trade}")

# # 打印年度回报率
# print("\n年度回报率:")
# print("=" * 80)
# print("{:<8} {:<12}".format("年份", "回报率"))
# for year, return_rate in annual_returns.items():
#     print("{:<8} {:<12.2%}".format(year, return_rate))

# 绘制结果
cerebro.plot(volume=False)
