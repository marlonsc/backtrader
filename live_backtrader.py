import backtrader as bt
from qmtbt import QMTStore
from datetime import datetime
from xtquant import xtdata, xtconstant
import math
import backtrader as bt
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        print("[连接状态] 与交易服务器连接断开")

    def on_stock_order(self, order):
        print("\n[委托单回调] 订单状态更新")
        print(f"证券代码: {order.stock_code}")
        print(f"订单状态: {order.order_status}")  # 需根据券商文档映射状态码含义
        print(f"系统订单号: {order.order_sysid}")

    def on_stock_asset(self, asset):
        print("\n[账户资产] 资金变动通知")
        print(f"账户ID: {asset.account_id}")
        print(f"可用资金: {asset.cash}")
        print(f"总资产估值: {asset.total_asset}")

    def on_stock_trade(self, trade):
        print("\n[成交记录] 交易已达成")
        print(f"账户ID: {trade.account_id}")
        print(f"证券代码: {trade.stock_code}")
        print(f"关联订单号: {trade.order_id}")

    def on_stock_position(self, position):
        print("\n[持仓变动] 头寸更新")
        print(f"证券代码: {position.stock_code}")
        print(f"当前持仓量: {position.volume}")

    def on_order_error(self, order_error):
        print("\n[委托失败] 订单提交错误")
        print(f"错误订单号: {order_error.order_id}")
        print(f"错误代码: {order_error.error_id}")
        print(f"错误详情: {order_error.error_msg}")  # 建议根据error_id映射具体原因

    def on_cancel_error(self, cancel_error):
        print("\n[撤单失败] 取消订单错误")
        print(f"目标订单号: {cancel_error.order_id}")
        print(f"错误代码: {cancel_error.error_id}")
        print(f"错误信息: {cancel_error.error_msg}")

    def on_order_stock_async_response(self, response):
        print("\n[异步响应] 委托请求已受理")
        print(f"账户ID: {response.account_id}")
        print(f"订单号: {response.order_id}")
        print(f"请求序列号: {response.seq}")

    def on_account_status(self, status):
        print("\n[账户状态] 登录/连接状态变化")
        print(f"账户ID: {status.account_id}")
        print(f"账户类型: {status.account_type}")  # 如普通户/信用户
        print(f"当前状态: {status.status}")        # 需映射状态码（如已连接/断开）

class my_broker:
    def __init__(self):
        self.path = r'E:\software\QMT\userdata_mini'  # 使用原始字符串避免转义
        self.session_id = 123456
        self.xt_trader = XtQuantTrader(self.path, self.session_id)
        # 连接QMT交易服务
        callback = MyXtQuantTraderCallback()
        self.acc = StockAccount('39131771')
        self.xt_trader.register_callback(callback)
        # 启动交易线程
        self.xt_trader.start()
        # 建立交易连接，返回0表示连接成功
        connect_result = self.xt_trader.connect()
        if connect_result != 0:
            import sys
            sys.exit('链接失败，程序即将退出 %d' % connect_result)
        # 对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功
        subscribe_result = self.xt_trader.subscribe(self.acc)
        if subscribe_result != 0:
            print('账号订阅失败 %d' % subscribe_result)

    def buy(self, stock_code, price, quantity):
        # 使用指定价下单，接口返回订单编号，后续可以用于撤单操作以及查询委托状态
        print("order using the fix price:")
        fix_result_order_id = self.xt_trader.order_stock(self.acc, stock_code, xtconstant.STOCK_BUY, quantity, xtconstant.FIX_PRICE,
                                                    price)
        print(fix_result_order_id)

    def sell(self, stock_code, price, quantity):
        #买之前得检查仓位
        print("order using the fix price:")
        fix_result_order_id = self.xt_trader.order_stock(self.acc, stock_code, xtconstant.STOCK_SELL, quantity, xtconstant.FIX_PRICE,
                                                    price)
        print(fix_result_order_id)

    def cancel_order(self,order_id):
        self.xt_trader.cancel_order_stock(self.acc, order_id)

    def quary(self):
        order=self.xt_trader.query_stock_orders(self.acc, False)
        return order






# Create a Stratey
class TestStrategy(bt.Strategy):


    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        # To keep track of pending orders
        self.order = None
        self.mbroker=my_broker()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        data = self.datas[0]
        stock_code = data._name
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                    # current close less than previous close

                    if self.dataclose[-1] < self.dataclose[-2]:
                        # previous close less than the previous close
                        
                        # self.mbroker.buy(stock_code= stock_code , price=1000,quantity=200)
                        # BUY, BUY, BUY!!! (with default parameters)
                        self.log('BUY CREATE, %.2f' % self.dataclose[0])

                        # Keep track of the created order to avoid a 2nd order
                        self.order = self.buy()


        else:

            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
                # self.mbroker.sell(stock_code=stock_code, price=100)

if __name__ == '__main__':

    store = QMTStore()
    code_list =['603429.SH']

    # 添加数据
    datas = store.getdatas(code_list=code_list, timeframe=bt.TimeFrame.Minutes, fromdate=datetime(2020, 1, 1),
                           todate=datetime(2021, 1, 1), live=False)

    for d in datas:
        # print(len(d))
        cerebro = bt.Cerebro(maxcpus=16)

        cerebro.adddata(d)
        # cerebro.broker = broker

        # 添加策略
        # buy_date = datetime(2022, 8, 1).date()  # 设置固定买入日期
        cerebro.addstrategy(TestStrategy)

        # cerebro.optstrategy

        # # 设置初始资金
        cerebro.broker.setcash(1000000.0)

        # 设置佣金
        cerebro.broker.setcommission(commission=0.001)


        cerebro.run()
        if cerebro.broker.getvalue() != 1000000.0:
            print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
